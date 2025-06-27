import re

class ClinicalInsightEngine:
    @staticmethod
    def analyze_vitals(text):
        """Analyze vital signs and lab results with clinical insights"""
        insights = []
        flags = []
        recommendations = []
        
        # Blood pressure analysis
        bp_pattern = r'BP:\s*(\d+)/(\d+)\s*mmHg'
        bp_match = re.search(bp_pattern, text, re.IGNORECASE)
        if bp_match:
            systolic = int(bp_match.group(1))
            diastolic = int(bp_match.group(2))
            
            if systolic >= 140 or diastolic >= 90:
                stage = "Stage 1" if systolic < 160 and diastolic < 100 else "Stage 2"
                flags.append(f"🩸 **Hypertension Alert**: Indicates {stage} hypertension (BP: {systolic}/{diastolic} mmHg)")
                recommendations.append("→ Lifestyle modification: Reduce salt intake (<5g/day), DASH diet")
                recommendations.append("→ Consider antihypertensive: Amlodipine 5mg OD or Telmisartan 40mg OD")
                recommendations.append("→ Monitor BP weekly for 4 weeks")
        
        # Glucose analysis
        glucose_pattern = r'(?:fasting glucose|blood sugar):?\s*(\d+)\s*mg/dL'
        glucose_match = re.search(glucose_pattern, text, re.IGNORECASE)
        if glucose_match:
            glucose = int(glucose_match.group(1))
            if glucose > 125:
                flags.append(f"🩺 **Diabetes Alert**: Fasting glucose elevated ({glucose} mg/dL) - suggests possible type 2 diabetes")
                recommendations.append("→ Confirm with HbA1c test and post-prandial glucose")
                recommendations.append("→ Initial management: Metformin 500mg BD with meals")
        
        # HbA1c analysis
        a1c_pattern = r'HbA1c:\s*(\d+\.?\d*)%'
        a1c_match = re.search(a1c_pattern, text, re.IGNORECASE)
        if a1c_match:
            a1c = float(a1c_match.group(1))
            if a1c >= 6.5:
                flags.append(f"⚠️ **Diabetes Confirmed**: HbA1c level ({a1c}%) indicates diabetes")
                recommendations.append("→ Initiate pharmacotherapy: Metformin 500mg BD")
                recommendations.append("→ Schedule screenings: Retinal exam, foot examination, renal function test")
            elif a1c >= 5.7:
                flags.append(f"🔔 **Pre-diabetes Alert**: HbA1c level ({a1c}%) indicates pre-diabetes")
                recommendations.append("→ Intensive lifestyle intervention: 7% weight loss, 150 min/week exercise")
        
        # Lipid profile analysis
        chol_pattern = r'Cholesterol:\s*(\d+)\s*mg/dL'
        chol_match = re.search(chol_pattern, text, re.IGNORECASE)
        if chol_match:
            cholesterol = int(chol_match.group(1))
            if cholesterol > 200:
                flags.append(f"🫀 **Hyperlipidemia Alert**: Elevated cholesterol ({cholesterol} mg/dL)")
                recommendations.append("→ Initiate statin therapy: Atorvastatin 10mg OD")
                recommendations.append("→ Recommend low-fat diet and aerobic exercise")
        
        # Return structured insights
        return {
            "flags": flags,
            "recommendations": recommendations
        }

    @staticmethod
    def generate_clinical_summary(entities, text):
        """Generate comprehensive clinical summary"""
        # Basic summary from entities
        summary = []
        if entities.get("CONDITIONS"):
            summary.append(f"**Conditions identified**: {', '.join(entities['CONDITIONS'])}")
        if entities.get("MEDICATIONS"):
            summary.append(f"**Medications mentioned**: {', '.join(entities['MEDICATIONS'])}")
        if entities.get("DOSAGES"):
            summary.append(f"**Dosages noted**: {', '.join(entities['DOSAGES'])}")
        
        # Add clinical insights
        insights = ClinicalInsightEngine.analyze_vitals(text)
        
        if insights["flags"]:
            summary.append("\n**Clinical Flags**\n" + "\n".join(insights["flags"]))
        
        if insights["recommendations"]:
            summary.append("\n**Recommendations**\n" + "\n".join(insights["recommendations"]))
        
        return "\n\n".join(summary)