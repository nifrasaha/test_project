INDIAN_CLINICAL_GUIDELINES = {
    "diabetes": {
        "diagnosis": {
            "criteria": [
                {
                    "test": "Fasting Glucose",
                    "threshold": 126,
                    "unit": "mg/dL",
                    "source": "API 2023"
                },
                {
                    "test": "HbA1c",
                    "threshold": 6.5,
                    "unit": "%",
                    "source": "RSSDI 2024"
                }
            ],
            "confirmatory": "Repeat test on another day"
        },
        "management": {
            "first_line": "Metformin + Lifestyle modification",
            "step_up": {
                "if_hba1c": ">8.5%",
                "add": "SGLT2i or Sulfonylurea"
            },
            "chennai_specific": [
                "Free screening camps at Apollo Hospitals every Sunday",
                "CMCHIS covers most oral hypoglycemics"
            ]
        }
    },
    "hypertension": {
        "staging": {
            "stage1": "130-139/80-89 mmHg",
            "stage2": "≥140/90 mmHg"
        },
        "treatment": {
            "first_line": "ACEI/ARB or CCB",
            "black_flags": [
                "Avoid ACEI in pregnancy",
                "Prefer ARBs in Tamil population (less cough)"
            ]
        }
    }
}