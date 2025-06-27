import json
import os
from datetime import datetime
import pandas as pd

class PatientDB:
    def __init__(self, db_path="data/patients"):
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        # Chennai-specific fields
        self.required_fields = {
            "basic": ["id", "name", "age", "gender", "phone"],
            "medical": ["blood_group", "allergies", "chronic_conditions"],
            "local": [
                "aadhaar",  # Commonly used ID in Chennai
                "area",    # Locality like Adyar/Kodambakkam
                "language"  # Tamil/English/Telugu
            ]
        }

    def _generate_id(self):
        """Generate Chennai-style ID (CLN-YYYY-XXXX)"""
        today = datetime.now()
        existing = len(os.listdir(self.db_path))
        return f"CLN-{today.year}-{existing+1:04d}"

    def create_patient(self, data):
        """Add new patient with Chennai-specific validation"""
        if not data.get("phone", "").startswith("+91"):
            data["phone"] = "+91" + str(data["phone"])
        
        # Auto-fill Chennai defaults
        data.setdefault("language", "Tamil")
        data.setdefault("blood_group", "B+")  # Most common in TN
        
        data['id'] = self._generate_id()
        patient_id = self._generate_id()
        file_path = os.path.join(self.db_path, f"{patient_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        return patient_id

    def get_patient(self, patient_id):
        """Retrieve patient record with error handling"""
        file_path = os.path.join(self.db_path, f"{patient_id}.json")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                data['id'] = patient_id # Add the ID to the returned dict
                return data
        except FileNotFoundError:
            return None

    def search_patients(self, query):
        """Chennai-optimized search (name/phone/locality)"""
        results = []
        for file in os.listdir(self.db_path):
            patient_id = file.replace(".json", "")
            data = self.get_patient(patient_id)
            if data:
                if (query.lower() in data.get("name", "").lower() or 
                    query in data.get("phone", "") or
                    query.lower() in data.get("area", "").lower()):
                    results.append(data)
        return results

    def add_medical_record(self, patient_id, report_data):
        """Append new medical report to patient history"""
        patient = self.get_patient(patient_id)
        if not patient:
            return False
        
        if "medical_history" not in patient:
            patient["medical_history"] = []
        
        patient["medical_history"].append({
            "date": datetime.now().strftime("%d/%m/%Y"),
            "report": report_data  # From report_parser.py
        })
        
        self._save_patient(patient_id, patient)
        return True

    def _save_patient(self, patient_id, data):
        file_path = os.path.join(self.db_path, f"{patient_id}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

# Example usage
if __name__ == "__main__":
    db = PatientDB()
    
    # Test patient (Chennai typical)
    patient_data = {
        "name": "Rajesh Kumar",
        "age": 45,
        "gender": "male",
        "phone": "+918123456789",
        "area": "T. Nagar",
        "chronic_conditions": ["diabetes"]
    }
    
    pid = db.create_patient(patient_data)
    print(f"Created patient {pid}")