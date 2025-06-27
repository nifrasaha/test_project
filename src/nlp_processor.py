import spacy
import json
import re

class MedicalNLPProcessor:
    def __init__(self):
        try:
            # Load clinical model
            self.nlp = spacy.load("en_ner_bc5cdr_md")
            
            # Add missing entity types
            self.ruler = self.nlp.add_pipe("entity_ruler")
            self._add_custom_patterns()
            
            # Configure processing
            self.nlp.max_length = 1000000
        except Exception as e:
            raise RuntimeError(f"Model loading failed: {str(e)}")

    def _add_custom_patterns(self):
        # Add Chennai-specific terms
        patterns = []
        
        # Body parts
        body_parts = ["heart", "liver", "kidney", "lung", "brain", "stomach", 
                      "intestine", "spine", "arm", "leg", "head", "chest",
                      "இதயம்", "கல்லீரல்", "சிறுநீரகம்"]  # Heart, Liver, Kidney in Tamil
        for part in body_parts:
            patterns.append({"label": "BODY_PART", "pattern": part})
        
        # Procedures
        procedures = ["biopsy", "MRI", "CT scan", "X-ray", "surgery", "endoscopy",
                     "colonoscopy", "angioplasty", "dialysis", "chemotherapy"]
        for proc in procedures:
            patterns.append({"label": "PROCEDURE", "pattern": proc})
        
        # Chennai medications
        chennai_meds = ["dolo", "crocin", "calpol", "combiflam", "limcee", "revital", "thyronorm"]
        for med in chennai_meds:
            patterns.append({"label": "MEDICATION", "pattern": med})
        
        self.ruler.add_patterns(patterns)

    def _extract_dosages(self, text):
        dosage_pattern = r'\b\d+\s*(?:mg|g|ml|mcg|IU|tablets?|drops|puffs|doses?)\b'
        return list(set(re.findall(dosage_pattern, text, flags=re.IGNORECASE)))

    def extract_entities(self, text):
        if not text.strip():
            return json.dumps({"error": "Empty input text"})
        
        try:
            doc = self.nlp(text)
            entities = {
                "CONDITIONS": [],
                "MEDICATIONS": [],
                "DOSAGES": self._extract_dosages(text),
                "BODY_PARTS": [],
                "PROCEDURES": []
            }
            
            # Process entities
            for ent in doc.ents:
                if ent.label_ == "DISEASE":
                    entities["CONDITIONS"].append(ent.text)
                elif ent.label_ == "CHEMICAL":
                    entities["MEDICATIONS"].append(ent.text)
                elif ent.label_ == "BODY_PART":
                    entities["BODY_PARTS"].append(ent.text)
                elif ent.label_ == "PROCEDURE":
                    entities["PROCEDURES"].append(ent.text)
            
            # Deduplicate and clean
            for key in entities:
                if isinstance(entities[key], list):
                    entities[key] = list(set(entities[key]))
            
            return json.dumps(entities, indent=2)
        
        except Exception as e:
            return json.dumps({"error": str(e)})