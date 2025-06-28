import sqlite3
import streamlit as st
from datetime import datetime, timedelta
import uuid
import json
import pandas as pd
from cryptography.fernet import Fernet
import os # Import os module to access environment variables

# Initialize encryption
# Load encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY not set in environment for patient_database.py")
cipher_suite = Fernet(ENCRYPTION_KEY)

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
    
    # Create medical profile table
    c.execute('''CREATE TABLE IF NOT EXISTS medical_profiles (
        patient_id TEXT PRIMARY KEY,
        blood_type TEXT,
        allergies TEXT,
        chronic_conditions TEXT,
        family_history TEXT,
        lifestyle TEXT,
        vaccination_history TEXT,
        last_updated DATETIME,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Create vitals table
    c.execute('''CREATE TABLE IF NOT EXISTS patient_vitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        date DATE,
        bp_systolic INTEGER,
        bp_diastolic INTEGER,
        heart_rate INTEGER,
        temperature REAL,
        weight REAL,
        height REAL,
        bmi REAL,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Create documents table
    c.execute('''CREATE TABLE IF NOT EXISTS medical_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        document_name TEXT,
        document_type TEXT,
        file_data BLOB,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    
    # Add Chennai-specific columns
    try:
        c.execute("ALTER TABLE patients ADD COLUMN area TEXT")
        c.execute("ALTER TABLE patients ADD COLUMN allergies TEXT")
        c.execute("ALTER TABLE patients ADD COLUMN preferred_hospital TEXT")
        c.execute("ALTER TABLE patients ADD COLUMN insurance TEXT")
    except sqlite3.OperationalError:
        pass  # Columns already exist
    
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

def check_prescription_safety(patient_id, medication):
    """Check if medication is safe for patient based on history"""
    conn = sqlite3.connect('patient_db.db')
    c = conn.cursor()
    
    # Get patient allergies
    c.execute("SELECT allergies FROM patients WHERE id = ?", (patient_id,))
    allergies_result = c.fetchone()
    # Ensure allergies is a string, even if NULL in DB or patient not found
    allergies = (allergies_result[0] or "") if allergies_result else ""
    
    # Check for contraindications
    warnings = []
    if "penicillin" in allergies.lower() and any(a in medication.lower() for a in ["penicillin", "amoxicillin", "ampicillin"]):
        warnings.append(f"⚠️ **Allergy Alert**: Patient has penicillin allergy - avoid {medication}")
    
    # Get patient conditions
    c.execute("SELECT condition FROM medical_history WHERE patient_id = ?", (patient_id,))
    conditions = [row[0].lower() for row in c.fetchall()]
    
    # Condition-based warnings
    if "asthma" in conditions and "beta-blocker" in medication.lower():
        warnings.append("⚠️ **Asthma Alert**: Beta-blockers may exacerbate asthma")
    
    conn.close()
    return warnings