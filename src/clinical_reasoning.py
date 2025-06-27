import re

# Existing ClinicalReasoningEngine...
class ClinicalReasoningEngine:
    DIAGNOSTIC_CRITERIA = {
        "hypertension": {
            "stages": [
                ("Stage 1", (130, 139), (80, 89)),
                ("Stage 2", (140, 180), (90, 120))
            ],
            "actions": {
                "Stage 1": "Lifestyle modifications + 3-month follow-up",
                "Stage 2": "Pharmacotherapy + monthly monitoring"
            }
        },
        "diabetes": {
            "fasting_glucose": (126, "mg/dL"),
            "hba1c": (6.5, "%"),
            "actions": [
                "Confirm with repeat testing",
                "Initiate metformin if HbA1c >7%",
                "Retinal screening within 1 year"
            ]
        }
    }

    def analyze_vitals(self, report_text: str):
        findings = []
        
        # Extract clinical data
        data = self._extract_clinical_data(report_text)
        
        # Apply diagnostic criteria
        if 'bp' in data:
            findings.extend(self._assess_hypertension(data['bp']))
        
        if 'glucose' in data or 'hba1c' in data:
            findings.extend(self._assess_diabetes(data.get('glucose'), data.get('hba1c')))
        
        return self._format_insights(findings)
    
    def _extract_clinical_data(self, text):
        """Extract structured data from text report"""
        data = {}
        
        # Blood pressure
        bp_match = re.search(r'BP:\s*(\d+)/(\d+)', text)
        if bp_match:
            data['bp'] = (int(bp_match.group(1)), int(bp_match.group(2)))
        
        # Glucose
        glucose_match = re.search(r'(?:glucose|sugar):?\s*(\d+)\s*mg/dL', text, re.I)
        if glucose_match:
            data['glucose'] = float(glucose_match.group(1))
        
        # HbA1c
        hba1c_match = re.search(r'HbA1c:\s*(\d+\.?\d*)%', text, re.I)
        if hba1c_match:
            data['hba1c'] = float(hba1c_match.group(1))
        
        return data
    
    def _assess_hypertension(self, bp):
        systolic, diastolic = bp
        criteria = self.DIAGNOSTIC_CRITERIA['hypertension']
        
        for stage, (s_range, d_range) in criteria['stages']:
            if (s_range[0] <= systolic <= s_range[1]) and (d_range[0] <= diastolic <= d_range[1]):
                return [
                    f"🩺 **Hypertension**: {stage} (BP: {systolic}/{diastolic} mmHg)",
                    f"📋 **Management**: {criteria['actions'][stage]}",
                    "🔍 **Next Steps**: Check for end-organ damage (retinopathy, proteinuria)"
                ]
        return []
    
    def _assess_diabetes(self, glucose=None, hba1c=None):
        criteria = self.DIAGNOSTIC_CRITERIA['diabetes']
        findings = []
        
        if glucose and glucose >= criteria['fasting_glucose'][0]:
            findings.append(f"🩸 **Diabetes Alert**: Fasting glucose {glucose} mg/dL (Threshold: {criteria['fasting_glucose'][0]})")
        
        if hba1c and hba1c >= criteria['hba1c'][0]:
            findings.append(f"🧪 **Diabetes Confirmed**: HbA1c {hba1c}% (Diagnostic: ≥{criteria['hba1c'][0]})")
        
        if findings:
            findings.extend([
                "💊 **Treatment**:",
                "- " + "\n- ".join(criteria['actions']),
                "📅 **Follow-up**: Repeat testing if borderline"
            ])
        
        return findings
    
    def _format_insights(self, findings):
        """Convert findings to formatted output"""
        if not findings:
            return "No significant clinical findings detected"
        
        return "\n\n".join(
            f"🔹 {item}" if not item.startswith(('🩺','🩸','🧪','💊','📅')) 
            else item 
            for item in findings
        )

# --- ChennaiClinicalReasoner below ---

from data.indian_guidelines import INDIAN_CLINICAL_GUIDELINES
from data.tamil_medical_terms import TAMIL_MEDICAL_TERMS

class ChennaiClinicalReasoner:
    def analyze_report(self, text: str):
        # Extract numerical values
        values = self._extract_values(text)
        
        # Convert Tamil terms
        translated_text = self._translate_tamil(text)
        
        # Get findings
        findings = []
        findings.extend(self._assess_diabetes(values))
        findings.extend(self._assess_hypertension(values))
        findings.extend(self._check_red_flags(translated_text))
        
        return self._format_report(findings)
    
    def _extract_values(self, text: str):
        values = {}
        # Glucose
        glucose_match = re.search(r'(?:glucose|sugar):?\s*(\d+)\s*mg/dL', text, re.I)
        if glucose_match:
            values['glucose'] = float(glucose_match.group(1))
        # BP
        bp_match = re.search(r'BP:\s*(\d+)/(\d+)', text)
        if bp_match:
            values['bp'] = (int(bp_match.group(1)), int(bp_match.group(2)))
        return values

    def _translate_tamil(self, text: str):
        for tamil, english in TAMIL_MEDICAL_TERMS['conditions'].items():
            text = text.replace(tamil, english)
        return text
    
    def _assess_diabetes(self, values):
        criteria = INDIAN_CLINICAL_GUIDELINES['diabetes']['diagnosis']
        findings = []
        
        if 'glucose' in values and values['glucose'] >= criteria['criteria'][0]['threshold']:
            findings.append({
                "type": "diabetes",
                "value": f"Fasting glucose: {values['glucose']} mg/dL",
                "interpretation": "Meets RSSDI diagnostic criteria",
                "action": INDIAN_CLINICAL_GUIDELINES['diabetes']['management']['first_line'],
                "chennai_notes": "Free screening at Rajiv Gandhi Govt. Hospital"
            })
        
        return findings

    def _assess_hypertension(self, values):
        findings = []
        if 'bp' in values:
            sys, dia = values['bp']
            # Example: Use Indian guidelines for hypertension
            if sys >= 140 or dia >= 90:
                findings.append({
                    "type": "hypertension",
                    "value": f"BP: {sys}/{dia} mmHg",
                    "interpretation": "Hypertension (Indian guideline)",
                    "action": "Lifestyle modification, consider medication",
                    "chennai_notes": "Apollo Hospitals offers BP clinics every Saturday"
                })
        return findings

    def _check_red_flags(self, text):
        red_flags = {
            "dengue": ["platelet <100,000", "fever >4 days"],
            "mi": ["chest pain", "st elevation"]
        }
        
        findings = []
        for condition, flags in red_flags.items():
            if any(f in text for f in flags):
                findings.append({
                    "type": "red_flag",
                    "condition": condition,
                    "urgency": "emergency" if condition == "mi" else "urgent",
                    "action": f"Refer to {'cardiology' if condition == 'mi' else 'general medicine'} immediately"
                })
        
        return findings

    def _format_report(self, findings):
        if not findings:
            return "No significant clinical findings detected"
        formatted = []
        for f in findings:
            if isinstance(f, dict):
                formatted.append(
                    f"🔹 {f.get('type','').title()}: {f.get('value','')}\n"
                    f"   - {f.get('interpretation','')}\n"
                    f"   - Action: {f.get('action','')}\n"
                    f"   - Chennai: {f.get('chennai_notes','')}"
                )
            else:
                formatted.append(str(f))
        return "\n\n".join(formatted)

# Example usage:
# engine = ClinicalReasoningEngine()
# print(engine.analyze_vitals("BP: 142/92 mmHg, Glucose: 128 mg/dL"))
# chennai_engine = ChennaiClinicalReasoner()
# print(chennai_engine.analyze_report("BP: 150/95 mmHg, glucose: 140