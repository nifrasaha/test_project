import sqlite3
import streamlit as st
from datetime import datetime, timedelta
import uuid
import json
import pandas as pd
from cryptography.fernet import Fernet

# Initialize encryption
ENCRYPTION_KEY = Fernet.generate_key()  # In production, store this securely
cipher_suite = Fernet(ENCRYPTION_KEY)

# Comprehensive medication database
DRUG_DATABASE = {
    "metformin": {
        "type": "Antidiabetic",
        "indications": "First-line therapy for type 2 diabetes",
        "safety": "Generally safe but contraindicated in renal impairment",
        "risks": "Lactic acidosis (renal impairment), B12 deficiency",
        "monitoring": "Renal function annually, B12 levels every 2 years",
        "alternatives": ["Glimepiride", "Sitagliptin", "Dapagliflozin"]
    },
    "ibuprofen": {
        "type": "NSAID",
        "indications": "Pain, inflammation, fever",
        "safety": "Avoid in renal impairment, heart failure, elderly",
        "risks": "GI bleeding, renal impairment, cardiovascular events",
        "monitoring": "Renal function with long-term use",
        "alternatives": ["Paracetamol", "Celecoxib", "Topical diclofenac"]
    },
    "warfarin": {
        "type": "Anticoagulant",
        "indications": "Atrial fibrillation, DVT prophylaxis",
        "safety": "Requires regular INR monitoring",
        "risks": "Bleeding, many drug and food interactions",
        "monitoring": "INR every 1-4 weeks",
        "alternatives": ["Dabigatran", "Apixaban", "Rivaroxaban"]
    }
}

DRUG_INTERACTIONS = {
    ("metformin", "ace inhibitors"): {
        "severity": "high",
        "risk": "Lactic acidosis and acute kidney injury",
        "mechanism": "ACE inhibitors impair renal function, reducing metformin clearance",
        "clinical_effects": "Nausea, vomiting, hyperventilation, tachycardia, hypotension",
        "management": (
            "1. Monitor renal function weekly\n"
            "2. Consider ARBs (losartan) as alternative antihypertensives\n"
            "3. Discontinue metformin if eGFR < 30 mL/min"
        ),
        "references": "ADA 2023 Guidelines"
    },
    ("metformin", "ibuprofen"): {
        "severity": "moderate",
        "risk": "Increased risk of renal impairment and lactic acidosis",
        "mechanism": "NSAIDs reduce renal function, impairing metformin excretion",
        "clinical_effects": "Elevated creatinine, metabolic acidosis",
        "management": (
            "1. Avoid concurrent use in renal impairment\n"
            "2. Use paracetamol instead of NSAIDs\n"
            "3. Monitor renal function if combined therapy necessary"
        ),
        "references": "Journal of Clinical Pharmacology 2024"
    },
    ("warfarin", "aspirin"): {
        "severity": "high",
        "risk": "Major bleeding events (GI bleed, intracranial hemorrhage)",
        "mechanism": "Additive antiplatelet effects",
        "clinical_effects": "Easy bruising, blood in stool, prolonged bleeding",
        "management": (
            "1. Avoid concurrent use\n"
            "2. For pain relief: Use paracetamol\n"
            "3. If essential: Maintain INR 2.0-2.5 with weekly monitoring"
        ),
        "references": "CHEST Guidelines 2024"
    },
    ("atorvastatin", "azithromycin"): {
        "severity": "moderate",
        "risk": "Rhabdomyolysis and myopathy",
        "mechanism": "Azithromycin inhibits statin metabolism via CYP3A4",
        "clinical_effects": "Muscle pain, weakness, dark urine",
        "management": (
            "1. Temporarily discontinue atorvastatin during antibiotic course\n"
            "2. Monitor CK levels if symptoms appear\n"
            "3. Alternative statin: Rosuvastatin (less CYP3A4 interaction)"
        ),
        "references": "American Heart Journal 2024"
    },
    ("penicillin", "allergy"): {
        "severity": "high",
        "risk": "Anaphylaxis, Stevens-Johnson syndrome",
        "mechanism": "Type I hypersensitivity reaction",
        "clinical_effects": "Hives, swelling, difficulty breathing, rash",
        "management": (
            "1. Avoid all penicillin-class antibiotics\n"
            "2. Use alternatives: Macrolides (azithromycin), Fluoroquinolones (levofloxacin)\n"
            "3. Patient should wear medical alert bracelet"
        ),
        "references": "Allergy and Clinical Immunology 2024"
    }
}

MEDICATION_ALIASES = {
    "dolo": "paracetamol",
    "crocin": "paracetamol",
    "calpol": "paracetamol",
    "combiflam": "ibuprofen + paracetamol",
    "limcee": "vitamin c",
    "thyronorm": "levothyroxine",
    "penicillin": "penicillin",
    "amoxicillin": "penicillin",
    "ampicillin": "penicillin"
}

# --- END DRUG DATABASE AND INTERACTIONS ---

# Database setup

# Database setup
def init_db():
    conn = sqlite3.connect('patient_db.db')
    c = conn.cursor()
    
    # Patients table
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        phone TEXT,
        address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Medical history table
    c.execute('''CREATE TABLE IF NOT EXISTS medical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        date DATE,
        condition TEXT,
        treatment TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Prescriptions table
    c.execute('''CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        date DATE,
        medication TEXT,
        dosage TEXT,
        duration TEXT,
        refills INTEGER,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Appointments table
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        date DATETIME,
        purpose TEXT,
        status TEXT DEFAULT 'Scheduled',
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    conn.commit()
    conn.close()

# Encrypt sensitive data
def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

# Decrypt data
def decrypt_data(encrypted_data):
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# Initialize database on import
init_db()

def check_interactions(medications):
    """Check for interactions with detailed risk information"""
    interactions_found = []
    
    # Normalize medication names
    normalized_meds = [MEDICATION_ALIASES.get(med.lower(), med.lower()) for med in medications]
    
    # Check for allergy interactions
    if "allergy" in normalized_meds and any(med in ["penicillin"] for med in normalized_meds):
        interactions_found.append(DRUG_INTERACTIONS[("penicillin", "allergy")].copy())
        interactions_found[-1]["drug_pair"] = "Penicillin + Allergy"
    
    # Check all pairs
    for i in range(len(normalized_meds)):
        for j in range(i + 1, len(normalized_meds)):
            med1, med2 = normalized_meds[i], normalized_meds[j]
            
            # Check both orderings
            interaction_key = (med1, med2)
            if interaction_key not in DRUG_INTERACTIONS:
                interaction_key = (med2, med1)
            
            if interaction_key in DRUG_INTERACTIONS:
                interaction = DRUG_INTERACTIONS[interaction_key].copy()
                interaction["drug_pair"] = f"{med1.title()} + {med2.title()}"
                interactions_found.append(interaction)
    
    return interactions_found

def get_drug_info(drug_name):
    """Get detailed safety information for a single drug"""
    normalized_drug = MEDICATION_ALIASES.get(drug_name.lower(), drug_name.lower())
    # Return drug info from DB, or a default dict to prevent KeyErrors in the UI.
    return DRUG_DATABASE.get(normalized_drug, {
        "type": "Information not available",
        "indications": "Not available",
        "safety": "No specific safety data",
        "risks": "No risk data available",
        "alternatives": []
    })

def get_drug_safety_notes(drug_list):
    """Generate comprehensive safety notes for medication list"""
    notes = []
    for drug in drug_list:
        info = get_drug_info(drug) # Reuse get_drug_info to get a complete dict
        # The 'safety' key is guaranteed to exist from get_drug_info's default dict
        notes.append(f"💊 **{drug.title()}**: {info['safety']}")
    return "\n\n".join(notes)