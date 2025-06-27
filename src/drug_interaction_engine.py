import re
import json
import os # Added import for os module
from typing import List, Dict

class DrugInteractionEngine:
    def __init__(self):
        # Load knowledge bases
        self.drug_db = self._load_drug_database()
        self.interaction_rules = self._load_interaction_rules()
        
    def _load_drug_database(self):
        """Enhanced drug database with pharmacological properties"""
        return {
            "metformin": {
                "class": "Biguanide",
                "targets": ["AMPK"],
                "metabolism": "Renal excretion",
                "side_effects": ["GI upset", "B12 deficiency"],
                "ci": ["eGFR<30", "Contrast media"]
            },
            "ibuprofen": {
                "class": "NSAID",
                "targets": ["COX-1", "COX-2"],
                "metabolism": "CYP2C9",
                "side_effects": ["GI bleed", "Renal impairment"],
                "ci": ["Peptic ulcer", "Aspirin allergy"]
            }
        }
    
    def _load_interaction_rules(self):
        """Rule-based interaction detection"""
        return [
            {
                "rule": lambda d1,d2: d1["metabolism"] == d2["metabolism"] and "CYP" in d1["metabolism"],
                "description": "Competitive metabolism via {metabolism}",
                "severity": "moderate",
                "action": "Monitor for toxicity or reduced efficacy"
            },
            {
                "rule": lambda d1,d2: "Renal excretion" in d1["metabolism"] and "Renal impairment" in d2["side_effects"],
                "description": "Increased risk of {d1} accumulation",
                "severity": "high",
                "action": "Adjust dose or use alternative"
            }
        ]
    
    def predict_interactions(self, drugs: List[str], patient_conditions: List[str] = []):
        """Predict interactions based on pharmacological principles"""
        results = []
        known_drugs = [d.lower() for d in drugs if d.lower() in self.drug_db]
        
        # Check all drug pairs
        for i in range(len(known_drugs)):
            for j in range(i+1, len(known_drugs)):
                drug1, drug2 = known_drugs[i], known_drugs[j]
                data1, data2 = self.drug_db[drug1], self.drug_db[drug2]
                
                # Apply interaction rules
                for rule in self.interaction_rules:
                    if rule["rule"](data1, data2):
                        desc = rule["description"].format(
                            metabolism=data1["metabolism"],
                            d1=drug1, d2=drug2
                        )
                        results.append({
                            "drug_pair": f"{drug1} + {drug2}",
                            "mechanism": desc,
                            "severity": rule["severity"],
                            "management": self._generate_management(drug1, drug2, rule, patient_conditions)
                        })
        
        return results
    
    def _generate_management(self, drug1, drug2, rule, conditions):
        """Generate personalized management plan"""
        management = [rule["action"]]
        
        # Add condition-specific advice
        if "Renal impairment" in conditions and "renal" in rule["description"].lower():
            management.append("Monitor creatinine weekly")
        
        # Suggest alternatives
        alternatives = {
            "ibuprofen": "Consider paracetamol or celecoxib",
            "metformin": "SGLT2 inhibitors may be safer in renal impairment"
        }
        for drug in [drug1, drug2]:
            if drug in alternatives:
                management.append(alternatives[drug])
        
        return "\n".join(management)

# --- Enhanced Engine Below ---

class EnhancedDrugInteractionEngine:
    def __init__(self):
        self.drug_db = self._load_drug_database()
        self.interaction_rules = self._load_interaction_rules()
        self.tamil_terms = self._load_tamil_terms()
    
    def _load_drug_database(self):
        with open(os.path.join(os.path.dirname(__file__), 'data', 'chennai_drugs.json')) as f:
            return {drug['name']: drug for drug in json.load(f)['drugs']}
    
    def _load_interaction_rules(self):
        # Placeholder for compatibility with original interface
        return []
    
    def _load_tamil_terms(self):
        from data.tamil_medical_terms import TAMIL_MEDICAL_TERMS
        return TAMIL_MEDICAL_TERMS
    
    def normalize_drug_name(self, name: str) -> str:
        """Convert brand/Tamil names to generic names"""
        name = name.lower()
        
        # Check Tamil terms first
        for tamil, english in self.tamil_terms['medications'].items():
            if tamil in name:
                return english
        
        # Check brand names
        for drug in self.drug_db.values():
            if name in [b.lower() for b in drug.get('brands', [])]:
                return drug['name']
        
        return name
    
    def predict_interactions(self, drugs: List[str], patient_conditions: List[str] = []):
        normalized_drugs = [self.normalize_drug_name(d) for d in drugs]
        valid_drugs = [d for d in normalized_drugs if d in self.drug_db]
        
        results = []
        for i in range(len(valid_drugs)):
            for j in range(i+1, len(valid_drugs)):
                drug1, drug2 = valid_drugs[i], valid_drugs[j]
                interactions = self._check_pair(drug1, drug2, patient_conditions)
                results.extend(interactions)
        
        return self._format_results(results, drugs)
    
    def _check_pair(self, drug1: str, drug2: str, conditions: List[str]):
        interactions = []
        data1, data2 = self.drug_db[drug1], self.drug_db[drug2]
        
        # Rule 1: Shared metabolism
        if data1.get('metabolism') and data2.get('metabolism'):
            if any(enz in data2['metabolism'] for enz in data1['metabolism'].split(',')):
                interactions.append({
                    "type": "metabolic",
                    "description": f"Both metabolized by {data1['metabolism']} → altered concentrations",
                    "severity": "moderate",
                    "management": "Monitor efficacy/toxicity, adjust doses"
                })
        
        # Rule 2: Additive toxicity
        if set(data1.get('side_effects', [])).intersection(data2.get('side_effects', [])):
            common = set(data1['side_effects']).intersection(data2['side_effects'])
            interactions.append({
                "type": "additive_toxicity",
                "description": f"Additive {', '.join(common)} risk",
                "severity": "high" if 'renal' in common else "moderate",
                "management": "Consider alternatives or enhanced monitoring"
            })
        
        # Condition-specific rules
        for condition in conditions:
            if condition == "renal_impairment" and ("renal" in data1.get('contraindications', "") or 
                                                  "renal" in data2.get('contraindications', "")):
                interactions.append({
                    "type": "renal_risk",
                    "description": f"Contraindicated in renal impairment",
                    "severity": "high",
                    "management": "Use safer alternatives: " + ", ".join(data1.get('alternatives', []))
                })
        
        return interactions
    
    def _format_results(self, interactions: List[Dict], original_names: List[str]):
        formatted = []
        for interaction in interactions:
            formatted.append({
                "drugs": original_names,
                "mechanism": interaction["description"],
                "risk_level": interaction["severity"].upper(),
                "clinical_impact": self._get_impact_statement(interaction),
                "management": interaction["management"],
                "chennai_resources": self._get_local_resources(interaction)
            })
        return formatted
    
    def _get_impact_statement(self, interaction):
        impacts = {
            "metabolic": "May lead to subtherapeutic effects or toxicity",
            "additive_toxicity": "Increased risk of adverse effects",
            "renal_risk": "Can worsen renal function → acute kidney injury"
        }
        return impacts.get(interaction["type"], "Potential clinically significant interaction")
    
    def _get_local_resources(self, interaction):
        resources = {
            "renal_risk": "Free renal function tests at GH Chennai every Wednesday",
            "metabolic": "Apollo Pharmacy offers therapeutic drug monitoring"
        }
        return resources.get(interaction["type"], "Consult Chennai Drug Information Center: 044-28293333")