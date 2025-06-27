import streamlit as st
import json
import pandas as pd
from nlp_processor import MedicalNLPProcessor
from drug_interaction_db import check_interactions, get_drug_info, get_drug_safety_notes
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import re
from openai import OpenAI # Assuming OpenAI is installed as a top-level package
from patient_database import encrypt_data, decrypt_data, check_prescription_safety
from clinical_insights import ClinicalInsightEngine
import sqlite3
from datetime import datetime, timedelta
from security import authenticate
import uuid
from cryptography.fernet import Fernet
from drug_interaction_engine import DrugInteractionEngine, EnhancedDrugInteractionEngine
# Set Streamlit page config at the very top of main.py
st.set_page_config(
    page_title="WeCare Medical Assistant",
    page_icon="❤️",
    layout="centered"
)

# Initialize Fernet key
print(Fernet.generate_key())

# Initialize NLP processor
@st.cache_resource
def load_processor():
    return MedicalNLPProcessor()

def init_db():
    """Initializes the SQLite database by creating tables if they don't exist."""
    conn = sqlite3.connect('patient_db.db')
    c = conn.cursor()

    # Create patients table
    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT,
            phone BLOB NOT NULL, -- BLOB for encrypted data
            address TEXT,
            area TEXT,
            preferred_hospital TEXT,
            insurance TEXT
        )
    """)

    # Create medical_history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            date TEXT NOT NULL,
            condition TEXT,
            treatment TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    # Create medical_profiles table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_profiles (
            patient_id TEXT PRIMARY KEY,
            blood_type TEXT,
            allergies TEXT,
            chronic_conditions TEXT,
            family_history TEXT,
            lifestyle TEXT,
            vaccination_history TEXT,
            last_updated TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    # Create patient_vitals table
    c.execute("""
        CREATE TABLE IF NOT EXISTS patient_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            date TEXT NOT NULL,
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            heart_rate INTEGER,
            temperature REAL,
            weight REAL,
            height REAL,
            bmi REAL,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    # Create prescriptions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            date TEXT NOT NULL,
            medication TEXT NOT NULL,
            dosage TEXT,
            duration TEXT,
            refills INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    # Create appointments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            date TEXT NOT NULL,
            purpose TEXT,
            status TEXT DEFAULT 'Scheduled',
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    # Create medical_documents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            document_name TEXT NOT NULL,
            document_type TEXT,
            file_data BLOB NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)

    conn.commit()
    conn.close()

processor = load_processor()

# Initialize OpenAI client (add your API key)
client = OpenAI(api_key="your-api-key")

# Initialize engines
@st.cache_resource
def load_engines():
    return {
        "drug": DrugInteractionEngine(),
        "clinical": ClinicalInsightEngine()
    }

engines = load_engines()

# Initialize enhanced engine
@st.cache_resource
def load_interaction_engine():
    return EnhancedDrugInteractionEngine()

interaction_engine = load_interaction_engine()

# Placeholder for monitoring plan function
def generate_monitoring_plan(med_list):
    return []

# Page navigation
def home_page():
    st.title("WeCare AI Assistant")
    # st.image("wecare_logo.png", width=200)  # Removed logo

    st.subheader("Intelligent Clinical Support for Chennai Doctors")
    
    # Chennai-specific welcome message
    st.markdown("""
    <div style="background-color:#e6f7ff; padding:20px; border-radius:10px; border-left:4px solid #0066cc">
        <h4>Chennai-Focused Healthcare AI</h4>
        <p>• Tamil language support • Local medication brands • Chennai hospital protocols</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📄 Report Analysis")
        st.write("Analyze medical reports and extract key insights")
        if st.button("Go to Report Analyzer", key="report_btn"):
            st.session_state.current_page = "report_analysis"
    with col2:
        st.markdown("### 💊 Drug Safety")
        st.write("Check medication safety and interactions")
        if st.button("Go to Drug Checker", key="drug_btn"):
            st.session_state.current_page = "drug_interaction"
    with col3:
        st.markdown("### 📁 Patient Records")
        st.write("Store and access patient medical history")
        if st.button("Go to Patient Records", key="patient_btn"):
            st.session_state.current_page = "patient_records"
    
    st.divider()
    st.markdown("### Chennai-Specific Features")
    st.write("- Tamil medical term recognition")
    st.write("- Local medication brand support (Dolo, Crocin)")
    st.write("- Chennai pharmacy integration")
    
    st.divider()
    st.caption("""
    **Disclaimer**: This AI assistant supports but does not replace professional medical judgment. 
    All final decisions should be made by qualified healthcare professionals.
    """)

def report_analysis_page():
    st.title("Medical Report Analyzer")
    st.caption("Upload medical reports or enter text for instant analysis")
    
    # Input options
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Upload Medical Report", 
                type=["txt", "pdf"],
                help="Supports TXT files and PDFs (text extraction)"
            )
        with col2:
            manual_text = st.text_area(
                "Or Enter Medical Notes Directly:", 
                height=200,
                placeholder="e.g., Patient with diabetes prescribed metformin 500mg twice daily..."
            )
    
    # Process input
    input_text = ""
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                for page in pdf_reader.pages:
                    input_text += page.extract_text() + "\n"
            except:
                st.error("PDF processing requires PyPDF2. Install with: pip install pypdf2")
                st.stop()
        else:  # Text file
            input_text = uploaded_file.getvalue().decode("utf-8")
    elif manual_text:
        input_text = manual_text
    
    # Analysis section
    if st.button("Analyze Report", type="primary") and input_text:
        with st.spinner("Analyzing medical content..."):
            # Process with NLP
            results = processor.extract_entities(input_text)
            entities = json.loads(results)
            
            # Error handling for NLP processing
            if "error" in entities:
                st.error(f"Analysis failed: {entities['error']}")
                return
            
            # Enhanced clinical analysis
            st.subheader("🩺 Clinical Interpretation") # This line is fine
            insights = engines["clinical"].analyze_vitals(input_text)
            if insights["flags"] or insights["recommendations"]:
                st.markdown("\n".join(insights["flags"]))
                st.markdown("\n".join(insights["recommendations"]))
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["Key Findings", "Highlighted Text", "Clinical Summary"])
            
            with tab1:
                st.subheader("Medical Entities Identified")
                # Create summary table
                summary_data = []
                for category, items in entities.items():
                    if isinstance(items, list) and items:  # Only show categories with findings
                        summary_data.append({
                            "Category": category,
                            "Count": len(items),
                            "Items": ", ".join(items)
                        })
                
                if summary_data:
                    st.dataframe(
                        pd.DataFrame(summary_data),
                        column_config={
                            "Items": st.column_config.ListColumn(
                                width="large",
                                help="Identified medical concepts"
                            )
                        },
                        hide_index=True
                    )
                else:
                    st.warning("No medical entities identified in the text")
            
            with tab2:
                st.subheader("Original Text with Highlights")
                # Color code entities
                color_map = {
                    "CONDITIONS": "#FF6B6B",
                    "MEDICATIONS": "#4D96FF",
                    "DOSAGES": "#6BCB77",
                    "BODY_PARTS": "#FFD93D",
                    "PROCEDURES": "#9C51E0"
                }
                
                # Create HTML with highlights
                highlighted_html = input_text
                for category, items in entities.items():
                    if isinstance(items, list):
                        for item in items:
                            # Escape special regex characters
                            escaped_item = re.escape(item)
                            highlighted_html = re.sub(
                                f"({escaped_item})", 
                                f"<span style='background-color: {color_map[category]}; padding: 2px; border-radius: 4px; font-weight: bold'>\\1</span>", 
                                highlighted_html, 
                                flags=re.IGNORECASE
                            )
                
                st.markdown(f"<div style='border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px;'>{highlighted_html}</div>", 
                            unsafe_allow_html=True)
            
            with tab3:
                st.subheader("Clinical Summary")
                
                # Generate readable summary
                summary_points = []
                if entities.get("CONDITIONS"):
                    summary_points.append(f"**Conditions identified**: {', '.join(entities['CONDITIONS'])}")
                if entities.get("MEDICATIONS"):
                    summary_points.append(f"**Medications mentioned**: {', '.join(entities['MEDICATIONS'])}")
                if entities.get("DOSAGES"):
                    summary_points.append(f"**Dosages noted**: {', '.join(entities['DOSAGES'])}")
                
                if summary_points:
                    st.write("\n\n".join(summary_points))
                else:
                    st.info("No significant medical concepts identified")
                
                # Condition-specific protocols
                if entities.get("CONDITIONS"):
                    if "diabetes" in [c.lower() for c in entities["CONDITIONS"]]:
                        with st.expander("Diabetes Management Protocol"):
                            st.markdown("""
                            **Initial Management**:
                            - Lifestyle: 150 min/week exercise, carb-controlled diet
                            - Medication: Metformin 500mg BD with meals
                            - Targets: Fasting &lt;130 mg/dL, HbA1c &lt;7%
                            
                            **Monitoring**:
                            - HbA1c every 3 months
                            - Annual retinal exam
                            - Foot examination at every visit
                            """)
                    
                    if "hypertension" in [c.lower() for c in entities["CONDITIONS"]]:
                        with st.expander("Hypertension Protocol"):
                            st.markdown("""
                            **Management Goals**:
                            - Target BP: &lt;140/90 mmHg (&lt;130/80 if diabetic)
                            - Lifestyle: DASH diet, &lt;5g salt/day, regular exercise
                            
                            **First-line Medications**:
                            - Age &lt;60: ACEI/ARB (Ramipril 5mg OD)
                            - Age ≥60: CCB (Amlodipine 5mg OD)
                            - Black patients: CCB or thiazide diuretic
                            """)
    
    # Back button
    st.divider()
    if st.button("← Back to Home"):
        st.session_state.current_page = "home"

def drug_interaction_page():
    st.title("Medication Safety Analyzer")
    st.caption("Check drug interactions and safety profiles")
    
    # Input medications
    medications = st.text_area(
        "Enter Medications (one per line or comma separated):",
        height=150,
        placeholder="e.g., Metformin 500mg\nIbuprofen 400mg",
        help="Enter brand or generic names of medications"
    )
    patient_id = st.text_input("Patient ID (optional for personalized analysis)")
    
    # Process input
    if st.button("Analyze Safety", type="primary") and medications:
        # Split medications
        med_list = []
        for line in medications.split('\n'):
            med_list.extend([m.strip() for m in line.split(',') if m.strip()])
        
        if med_list:
            # Get patient conditions from medical history
            conditions = []
            if patient_id:
                conn = sqlite3.connect('patient_db.db')
                c = conn.cursor()
                c.execute("SELECT condition FROM medical_history WHERE patient_id=?", (patient_id,))
                conditions = [row[0] for row in c.fetchall()]
                conn.close()
            
            # Enhanced analysis
            results = interaction_engine.predict_interactions(med_list, conditions)
            
            if results:
                st.subheader("🧪 Advanced Interaction Analysis")
                for interaction in results:
                    with st.expander(
                        f"🔬 {' + '.join(interaction['drugs'])} - {interaction['risk_level']} RISK", 
                        expanded=True
                    ):
                        st.markdown(f"""
                        **Mechanism**: {interaction['mechanism']}
                        
                        **Clinical Impact**:  
                        {interaction['clinical_impact']}
                        
                        **Management**:  
                        {interaction['management']}
                        
                        **Chennai Resources**:  
                        {interaction['chennai_resources']}
                        """)
                        
                        # Show alternatives
                        st.markdown("### 💊 Safer Alternatives")
                        for drug in interaction['drugs']:
                            generic = interaction_engine.normalize_drug_name(drug)
                            if generic in interaction_engine.drug_db:
                                alts = interaction_engine.drug_db[generic].get('alternatives', [])
                                if alts:
                                    st.write(f"For **{drug}**: {', '.join(alts)}")
            else:
                st.success("✅ No dangerous drug interactions detected")
        else:
            st.warning("Please enter at least one medication")
    
    # Back button
    st.divider()
    if st.button("← Back to Home"):
        st.session_state.current_page = "home"

def ai_safety_analysis(medications, interactions):
    """Get AI-powered safety recommendations"""
    prompt = f"""
    As a medical safety expert in Chennai, analyze these medications: {", ".join(medications)}.
    Detected interactions: {interactions if interactions else 'None'}.
    Provide concise safety recommendations considering:
    1. Common Chennai patient profiles
    2. Local availability of alternatives
    3. Hot weather considerations
    4. Format: bullet points with emojis
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a clinical pharmacist specializing in drug safety in South India"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except:
        return "AI analysis unavailable"

def patient_records_page():
    authenticate()  # Require authentication
    st.title("🩺 Comprehensive Patient Records")
    st.caption("Complete EHR system for Chennai medical practices")
    
    # Page navigation with icons
    tabs = st.tabs([
        "👤 Add Patient", 
        "🔍 Search Records", 
        "💊 Medical Profile",
        "📊 Vitals Tracker",
        "📝 Prescriptions",
        "📅 Appointments",
        "📂 Documents"
    ])
    
    with tabs[0]:  # Add Patient
        st.subheader("Register New Patient")
        with st.form("patient_form"):
            name = st.text_input("Full Name*")
            age = st.number_input("Age*", min_value=0, max_value=120)
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"])
            phone = st.text_input("Phone Number*")
            address = st.text_area("Address (Chennai Area)")
            
            # Enhanced Chennai fields
            with st.expander("Chennai-Specific Details"):
                areas = ["Adyar", "Anna Nagar", "T. Nagar", "Velachery", "Nungambakkam", "Tambaram", "Chromepet"]
                hospitals = ["Apollo", "Kauvery", "MIOT", "Fortis", "Global", "SIMS", "Government Hospital"]
                
                col1, col2 = st.columns(2)
                with col1:
                    area = st.selectbox("Residential Area", areas)
                with col2:
                    preferred_hospital = st.selectbox("Preferred Hospital", hospitals)
                
                insurance = st.selectbox("Health Insurance", [
                    "None", "Star Health", "Apollo Munich", "ICICI Lombard", 
                    "Government Scheme", "Other"
                ])
            
            submitted = st.form_submit_button("Save Patient Record")
            
            if submitted:
                if not all([name, age, phone]):
                    st.error("Please fill required fields (*)")
                else:
                    conn = sqlite3.connect('patient_db.db')
                    c = conn.cursor()
                    patient_id = f"CHN-{datetime.now().strftime('%Y%m')}-{str(uuid.uuid4())[:8]}"
                    c.execute("""INSERT INTO patients (id, name, age, gender, phone, address, area, preferred_hospital, insurance) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (patient_id, name, age, gender, encrypt_data(phone), address, area, preferred_hospital, insurance)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Patient registered! ID: {patient_id}")
    
    with tabs[1]:  # Search Records
        st.subheader("Search Patient Records")
        search_term = st.text_input("Search by Name or Patient ID")
        
        if search_term:
            conn = sqlite3.connect('patient_db.db')
            c = conn.cursor()
            
            # Search patients
            c.execute("""SELECT id, name, age, gender, phone, address, area, preferred_hospital, insurance 
                         FROM patients WHERE name LIKE ? OR id LIKE ?""",
                (f"%{search_term}%", f"%{search_term}%")
            )
            patients = c.fetchall()
            
            if patients:
                for patient in patients:
                    # patient[0]=id, patient[1]=name, patient[2]=age, patient[3]=gender, patient[4]=phone, patient[5]=address, patient[6]=area, patient[7]=preferred_hospital, patient[8]=insurance
                    with st.expander(f"{patient[1]} (ID: {patient[0]})"):
                        st.write(f"**Age**: {patient[2]} | **Gender**: {patient[3]}")
                        st.write(f"**Phone**: {decrypt_data(patient[4])}")
                        st.write(f"**Address**: {patient[5]}")
                        
                        # Medical history
                        st.subheader("Medical History")
                        c.execute(
                            "SELECT date, condition, treatment, notes FROM medical_history WHERE patient_id = ?",
                            (patient[0],)
                        )
                        history = c.fetchall()
                        
                        if history:
                            history_df = pd.DataFrame(history, columns=["Date", "Condition", "Treatment", "Notes"])
                            st.dataframe(history_df, hide_index=True)
                        else:
                            st.write(f"**Area**: {patient[6]}")
                            st.write(f"**Preferred Hospital**: {patient[7]}")
                            st.write(f"**Insurance**: {patient[8]}")
                            st.info("No medical history recorded")
                        
                        # Add new history entry
                        with st.form(f"history_form_{patient[0]}"):
                            st.write("Add Medical History Entry")
                            entry_date = st.date_input("Date")
                            condition = st.text_input("Condition")
                            treatment = st.text_input("Treatment")
                            notes = st.text_area("Notes")
                            if st.form_submit_button("Add Entry"):
                                c.execute(
                                    "INSERT INTO medical_history (patient_id, date, condition, treatment, notes) VALUES (?, ?, ?, ?, ?)",
                                    (patient[0], entry_date.strftime("%Y-%m-%d"), condition, treatment, notes)
                                )
                                conn.commit()
                                st.success("Entry added!")
            else:
                st.warning("No patients found")
            
            conn.close()
    
    with tabs[2]:  # Medical Profile
        st.subheader("Comprehensive Medical Profile")
        patient_id = st.text_input("Enter Patient ID", key="med_profile_id")
        
        if patient_id:
            conn = sqlite3.connect('patient_db.db')
            c = conn.cursor()
            
            # Check if profile exists
            c.execute("SELECT * FROM medical_profiles WHERE patient_id = ?", (patient_id,))
            profile = c.fetchone()
            
            # Get patient name
            c.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
            patient_name = c.fetchone()
            if patient_name:
                st.subheader(f"Medical Profile: {patient_name[0]}")
            else:
                st.error("Patient not found.")
                conn.close()
                return
            
            with st.form("medical_profile_form"):
                # Blood type with Indian prevalence
                blood_type = st.selectbox("Blood Type", [
                    "", "O+ (Most common)", "B+", "A+", "AB+", 
                    "O- (Rare)", "B-", "A-", "AB-"
                ], index=["", "O+ (Most common)", "B+", "A+", "AB+", "O- (Rare)", "B-", "A-", "AB-"].index(profile[1]) if profile and profile[1] else 0)
                
                # Allergies common in Chennai
                allergies = st.text_area("Allergies", help="e.g., Penicillin, Dust mites, Seafood", value=profile[2] if profile else "")
                
                # Chronic conditions prevalent in South India
                chronic_conditions_options = [
                    "Diabetes", "Hypertension", "CAD", "Asthma",
                    "Thyroid Disorder", "Arthritis", "CKD", "COPD"
                ]
                chronic_conditions_selected = st.multiselect("Chronic Conditions", chronic_conditions_options, default=profile[3].split(', ') if profile and profile[3] else [])
                
                # Family history with Indian context
                family_history = st.text_area("Family History", 
                    placeholder="e.g., Father: Diabetes at 45, Mother: Hypertension", value=profile[4] if profile else "")
                
                # Lifestyle factors
                lifestyle_parts = profile[5].split(', ') if profile and profile[5] else ["Smoking: Never", "Alcohol: Never", "Diet: Vegetarian", "Exercise: Sedentary"]
                smoking_val = lifestyle_parts[0].split(': ')[1] if len(lifestyle_parts) > 0 else "Never"
                alcohol_val = lifestyle_parts[1].split(': ')[1] if len(lifestyle_parts) > 1 else "Never"
                diet_val = lifestyle_parts[2].split(': ')[1] if len(lifestyle_parts) > 2 else "Vegetarian"
                exercise_val = lifestyle_parts[3].split(': ')[1] if len(lifestyle_parts) > 3 else "Sedentary"

                col1, col2 = st.columns(2)
                with col1:
                    smoking = st.selectbox("Smoking", ["Never", "Former", "Current"], index=["Never", "Former", "Current"].index(smoking_val))
                    alcohol = st.selectbox("Alcohol", ["Never", "Occasional", "Regular"], index=["Never", "Occasional", "Regular"].index(alcohol_val))
                with col2:
                    diet = st.selectbox("Diet", ["Vegetarian", "Non-vegetarian", "Vegan"], index=["Vegetarian", "Non-vegetarian", "Vegan"].index(diet_val))
                    exercise = st.selectbox("Exercise", ["Sedentary", "Light", "Moderate", "Intense"], index=["Sedentary", "Light", "Moderate", "Intense"].index(exercise_val))
                
                lifestyle = f"Smoking: {smoking}, Alcohol: {alcohol}, Diet: {diet}, Exercise: {exercise}"
                
                # Vaccination history
                vaccinations_options = [
                    "BCG", "Hepatitis B", "OPV", "DPT", 
                    "MMR", "Typhoid", "COVID-19", "Influenza"
                ]
                vaccinations_selected = st.multiselect("Vaccinations", vaccinations_options, default=profile[6].split(', ') if profile and profile[6] else [])
                
                if st.form_submit_button("Save Medical Profile"):
                    # Convert lists to strings
                    chronic_str = ", ".join(chronic_conditions_selected)
                    vacc_str = ", ".join(vaccinations_selected)
                    
                    if profile:
                        # Update existing profile
                        c.execute("""UPDATE medical_profiles SET 
                            blood_type=?, allergies=?, chronic_conditions=?, 
                            family_history=?, lifestyle=?, vaccination_history=?, 
                            last_updated=CURRENT_TIMESTAMP
                            WHERE patient_id=?""",
                            (blood_type, allergies, chronic_str, family_history, 
                             lifestyle, vacc_str, patient_id)
                        )
                    else:
                        # Create new profile
                        c.execute("""INSERT INTO medical_profiles 
                            (patient_id, blood_type, allergies, chronic_conditions, 
                            family_history, lifestyle, vaccination_history, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                            (patient_id, blood_type, allergies, chronic_str, 
                             family_history, lifestyle, vacc_str)
                        )
                    conn.commit()
                    st.success("Medical profile saved!")
                    st.rerun() # Rerun to display updated profile
            
            # Display existing profile
            if profile:
                st.divider()
                st.subheader("Current Medical Profile")
                
                cols = st.columns(2)
                with cols[0]:
                    st.metric("Blood Type", profile[1] or "Not recorded")
                    st.info(f"**Allergies**: {profile[2] or 'None'}")
                    st.info(f"**Chronic Conditions**: {profile[3] or 'None'}")
                
                with cols[1]:
                    st.info(f"**Family History**: {profile[4] or 'Not recorded'}")
                    st.info(f"**Lifestyle**: {profile[5] or 'Not recorded'}")
                    st.info(f"**Vaccinations**: {profile[6] or 'None'}")
                
                st.caption(f"Last updated: {profile[7]}")

                # Add Chennai-specific health recommendations
                st.divider()
                st.subheader("Chennai Health Advisory")
                
                # Air quality advisory
                st.info("""
                **Air Quality Alert**: Chennai AQI is 120 (Moderate) today.
                - Asthma patients should limit outdoor activities
                - Use N95 masks when outside
                """)
                
                # Seasonal health alerts
                today = datetime.now()
                if today.month in [6, 7, 8, 9]:
                    st.warning("""
                    **Monsoon Health Advisory**:
                    - Increased risk of dengue and waterborne diseases
                    - Use mosquito repellents
                    - Drink boiled water
                    """)
                
                # Disease outbreak alerts
                if "diabetes" in (profile[3] or "").lower():
                    st.info("""
                    **Diabetes Care in Chennai**:
                    - Free screening camps every Saturday at Apollo Hospitals
                    - Tamil Nadu govt. provides insulin at 50% discount
                    """)
            
            conn.close()
    
    with tabs[3]:  # Vitals Tracker
        st.subheader("Patient Vitals Tracker")
        patient_id = st.text_input("Enter Patient ID", key="vitals_id")
        
        if patient_id:
            conn = sqlite3.connect('patient_db.db')
            c = conn.cursor()
            
            # Get patient info
            c.execute("SELECT name, age, gender FROM patients WHERE id = ?", (patient_id,))
            patient = c.fetchone()
            if patient:
                st.subheader(f"Vitals for {patient[0]} ({patient[1]} {patient[2]})")
            else:
                st.error("Patient not found.")
                conn.close()
                return
            
            with st.form("vitals_form"):
                st.write("Record New Vitals")
                
                col1, col2 = st.columns(2)
                with col1:
                    date = st.date_input("Date", value=datetime.now().date())
                    bp_systolic = st.number_input("BP Systolic", min_value=50, max_value=250, value=120)
                    heart_rate = st.number_input("Heart Rate (bpm)", min_value=30, max_value=200, value=70)
                    height = st.number_input("Height (cm)", min_value=50, max_value=250, value=170)
                with col2:
                    bp_diastolic = st.number_input("BP Diastolic", min_value=30, max_value=150, value=80)
                    temperature = st.number_input("Temperature (°C)", min_value=35.0, max_value=42.0, step=0.1, value=37.0)
                    weight = st.number_input("Weight (kg)", min_value=10, max_value=300, value=70)
                
                notes = st.text_area("Clinical Notes")
                
                if st.form_submit_button("Save Vitals"):
                    # Calculate BMI
                    bmi = weight / ((height/100) ** 2) if height > 0 else 0
                    
                    c.execute("""INSERT INTO patient_vitals 
                        (patient_id, date, bp_systolic, bp_diastolic, heart_rate, 
                        temperature, weight, height, bmi, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (patient_id, date.strftime("%Y-%m-%d"), bp_systolic, bp_diastolic, 
                         heart_rate, temperature, weight, height, round(bmi, 1), notes)
                    )
                    conn.commit()
                    st.success("Vitals recorded!")
                    st.rerun() # Rerun to display updated vitals history
            
            # Vitals history
            st.divider()
            st.subheader("Vitals History")
            c.execute("SELECT date, bp_systolic, bp_diastolic, heart_rate, temperature, weight, bmi FROM patient_vitals WHERE patient_id = ? ORDER BY date DESC", (patient_id,))
            vitals = c.fetchall()
            
            if vitals:
                vitals_df = pd.DataFrame(vitals, columns=["Date", "BP Sys", "BP Dia", "HR", "Temp", "Weight", "BMI"])
                vitals_df["Date"] = pd.to_datetime(vitals_df["Date"]) # Convert to datetime for plotting
                
                # Add status indicators
                def bp_status(row):
                    if row["BP Sys"] > 140 or row["BP Dia"] > 90:
                        return "🟥 Hypertension"
                    elif row["BP Sys"] < 90 or row["BP Dia"] < 60:
                        return "🟦 Hypotension"
                    return "🟩 Normal"
                
                def bmi_status(row):
                    if row["BMI"] == 0:
                        return ""
                    elif row["BMI"] < 18.5:
                        return "Underweight"
                    elif row["BMI"] < 25:
                        return "Normal"
                    elif row["BMI"] < 30:
                        return "Overweight"
                    return "Obese"
                
                vitals_df["BP Status"] = vitals_df.apply(bp_status, axis=1)
                vitals_df["Weight Status"] = vitals_df.apply(bmi_status, axis=1)
                
                st.dataframe(
                    vitals_df,
                    column_config={
                        "Date": st.column_config.DateColumn(),
                        "BP Sys": st.column_config.ProgressColumn(min_value=50, max_value=200),
                        "BP Dia": st.column_config.ProgressColumn(min_value=30, max_value=150),
                        "BMI": st.column_config.ProgressColumn(min_value=15, max_value=40)
                    },
                    hide_index=True
                )
                
                # Show trends
                if len(vitals) > 1:
                    st.subheader("Trend Analysis")
                    trend_col = st.selectbox("Select parameter to visualize", ["BP Sys", "BP Dia", "Weight", "BMI"])
                    st.line_chart(vitals_df.set_index("Date")[trend_col])
            else:
                st.info("No vitals recorded yet")
            
            conn.close()
    
    with tabs[4]:  # Prescriptions
        st.subheader("Prescription Management")
        patient_id = st.text_input("Patient ID")
        
        if patient_id:
            conn = sqlite3.connect('patient_db.db')
            c = conn.cursor()
            
            # Verify patient exists
            c.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
            patient = c.fetchone()
            
            if patient:
                st.success(f"Patient: {patient[0]}")
                
                # Current prescriptions
                st.subheader("Active Prescriptions")
                c.execute(
                    "SELECT date, medication, dosage, duration, refills FROM prescriptions WHERE patient_id = ?",
                    (patient_id,)
                )
                prescriptions = c.fetchall()
                
                if prescriptions:
                    pres_df = pd.DataFrame(prescriptions, columns=["Date", "Medication", "Dosage", "Duration", "Refills"])
                    st.dataframe(pres_df, hide_index=True)
                else:
                    st.info("No active prescriptions")
                
                # New prescription form
                with st.form("prescription_form"):
                    st.subheader("New Prescription")
                    med_name = st.text_input("Medication*")
                    dosage = st.text_input("Dosage* (e.g., 500mg)")
                    duration = st.text_input("Duration* (e.g., 7 days)")
                    refills = st.number_input("Refills", min_value=0, max_value=5)
                    notes = st.text_area("Instructions")
                    
                    if st.form_submit_button("Issue Prescription"):
                        if not all([med_name, dosage, duration]):
                            st.error("Please fill required fields (*)")
                        else:
                            # Check for safety issues
                            safety_warnings = check_prescription_safety(patient_id, med_name)
                            if safety_warnings:
                                for warning in safety_warnings:
                                    st.error(warning)
                                if not st.checkbox("I understand the risks and wish to proceed"):
                                    st.stop()
                            
                            # ... save prescription ...
                            c.execute(
                                "INSERT INTO prescriptions (patient_id, date, medication, dosage, duration, refills) VALUES (?, ?, ?, ?, ?, ?)",
                                (patient_id, datetime.now().strftime("%Y-%m-%d"), med_name, dosage, duration, refills)
                            )
                            conn.commit()
                            st.success("Prescription issued!")
                            st.rerun() # Rerun to display updated prescriptions
            else:
                st.error("Invalid Patient ID")
            
            if st.button("Send to Pharmacy"):
                st.info("Prescription sent to nearest Apollo Pharmacy in Adyar")
            conn.close()
    
    with tabs[5]:  # Appointments
        st.subheader("Appointment Scheduling")
        
        # New appointment
        with st.expander("Schedule New Appointment"):
            patient_id = st.text_input("Patient ID*")
            purpose = st.text_input("Purpose*")
            appt_date = st.date_input("Date*")
            appt_time = st.time_input("Time*")
            
            if st.button("Schedule Appointment"):
                if not all([patient_id, purpose]):
                    st.error("Please fill required fields (*)")
                else:
                    conn = sqlite3.connect('patient_db.db')
                    c = conn.cursor()
                    
                    # Verify patient exists
                    c.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
                    patient = c.fetchone()
                    
                    if patient:
                        appt_datetime = f"{appt_date.strftime('%Y-%m-%d')} {appt_time.strftime('%H:%M')}"
                        c.execute(
                            "INSERT INTO appointments (patient_id, date, purpose) VALUES (?, ?, ?)",
                            (patient_id, appt_datetime, purpose)
                        )
                        conn.commit()
                        st.success(f"Appointment scheduled for {patient[0]} on {appt_datetime}")
                    else:
                        st.error("Invalid Patient ID")
                    
                    st.rerun() # Rerun to display updated appointments
                    
                    conn.close()
        
        # View appointments
        st.subheader("Upcoming Appointments")
        conn = sqlite3.connect('patient_db.db')
        c = conn.cursor()
        
        # Today and next 7 days
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        c.execute(
            """SELECT a.id, p.name, a.date, a.purpose, a.status 
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE date BETWEEN ? AND ?
            ORDER BY a.date""",
            (start_date, end_date)
        )
        appointments = c.fetchall()
        
        if appointments:
            appt_df = pd.DataFrame(appointments, columns=["ID", "Patient", "Date", "Purpose", "Status"])
            
            # Add action buttons
            appt_df["Actions"] = "Update"
            
            # Display as editable dataframe
            edited_df = st.data_editor(
                appt_df,
                column_definitions={
                    "Date": st.column_definitions.DateColumn(
                        "Date",
                        min_value=datetime.now().date(),
                        max_value=(datetime.now() + timedelta(days=30)).date(),
                        default=datetime.now().date()
                    ),
                    "Status": st.column_definitions.SelectColumn(
                        "Status",
                        options=["Scheduled", "Completed", "Cancelled"],
                        default="Scheduled"
                    ),
                    "Actions": st.column_definitions.ButtonColumn(
                        "Actions",
                        text="Update",
                        key="update_btn",
                        disabled=False
                    )
                },
                hide_index=True,
                editable=True
            )
            
            # Handle updates
            for i, row in edited_df.iterrows():
                if row["Actions"] == "Update":
                    with st.expander(f"Update Appointment {row['ID']}"):
                        new_status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"], index=["Scheduled", "Completed", "Cancelled"].index(row["Status"]))
                        new_date = st.date_input("Date", value=datetime.strptime(row["Date"], "%Y-%m-%d").date(), min_value=datetime.now().date(), max_value=(datetime.now() + timedelta(days=30)).date())
                        new_purpose = st.text_input("Purpose", value=row["Purpose"])
                        
                        if st.button("Save Changes"):
                            # Update database
                            c.execute(
                                "UPDATE appointments SET date = ?, purpose = ?, status = ? WHERE id = ?",
                                (new_date.strftime("%Y-%m-%d"), new_purpose, new_status, row["ID"])
                            )
                            conn.commit()
                            st.success("Appointment updated!")
        
        else:
            st.info("No upcoming appointments")
        
        if st.button("Send SMS Reminder"):
            st.success("Appointment reminder sent to patient's phone")
        conn.close()
    
    with tabs[6]:  # Documents
        st.subheader("Medical Document Management")
        patient_id = st.text_input("Enter Patient ID", key="docs_id")
        
        if patient_id:
            conn = sqlite3.connect('patient_db.db')
            c = conn.cursor()
            
            # Check if patient exists
            c.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
            patient_name = c.fetchone()
            if not patient_name:
                st.error("Patient not found.")
                conn.close()
                return
            st.subheader(f"Documents for {patient_name[0]}")

            # Upload new document
            uploaded_file = st.file_uploader("Upload Medical Document", type=["pdf", "jpg", "png"])
            if uploaded_file:
                document_name = st.text_input("Document Name", value=uploaded_file.name)
                doc_type = st.selectbox("Document Type", ["Lab Report", "Scan", "Prescription", "Discharge Summary", "Other"])
                
                if st.button("Save Document"):
                    file_data = uploaded_file.getvalue()
                    c.execute("""INSERT INTO medical_documents 
                        (patient_id, document_name, document_type, file_data)
                        VALUES (?, ?, ?, ?)""",
                        (patient_id, document_name, doc_type, file_data)
                    )
                    conn.commit()
                    st.success("Document saved!")
                    st.rerun() # Rerun to display updated document list
            
            # Document list
            st.divider()
            st.subheader("Stored Documents")
            c.execute("SELECT id, document_name, document_type, uploaded_at, file_data FROM medical_documents WHERE patient_id = ? ORDER BY uploaded_at DESC", (patient_id,))
            documents = c.fetchall()
            
            if documents:
                for doc in documents:
                    with st.expander(f"{doc[1]} ({doc[2]}) - {doc[3].split()[0]}"):
                        col1, col2 = st.columns([1,3])
                        with col1:
                            st.download_button(
                                label="Download",
                                data=doc[4],  # Actual file data
                                file_name=doc[1],
                                mime="application/octet-stream",
                                key=f"download_{doc[0]}"
                            )
                        with col2:
                            if st.button("Delete", key=f"delete_{doc[0]}"):
                                c.execute("DELETE FROM medical_documents WHERE id = ?", (doc[0],))
                                conn.commit()
                                st.rerun()
            else:
                st.info("No documents stored")
            
            conn.close()
    
    # Back button
    st.divider()
    if st.button("← Back to Home", key="back_to_home_patient_records"):
        st.session_state.current_page = "home"

# Main app
def main():
    st.set_page_config(
        page_title="MedAI Assistant",
        layout="centered",
        page_icon="⚕️"
    )
    init_db() # Initialize database tables
    
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    # Page routing
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "report_analysis":
        report_analysis_page()
    elif st.session_state.current_page == "drug_interaction":
        drug_interaction_page()
    elif st.session_state.current_page == "patient_records":
        patient_records_page()

if __name__ == "__main__":
    main()
