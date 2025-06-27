import re
import json
from PyPDF2 import PdfReader
import os # Added import for os module
from nlp_processor import MedicalNLPProcessor  # Import our NLP processor

class MedicalReportParser:
    def __init__(self):
        self.nlp_processor = MedicalNLPProcessor()
        self.section_patterns = {
            "patient_info": r"(PATIENT DETAILS|PATIENT INFORMATION|பொதுவான விவரங்கள்)",
            "clinical_history": r"(CLINICAL HISTORY|HISTORY OF PRESENT ILLNESS|நோய் வரலாறு)",
            "findings": r"(FINDINGS|OBSERVATIONS|கண்டறியப்பட்டவை)",
            "impressions": r"(IMPRESSION|CONCLUSION|முடிவுரை)"
        }
        self.chennai_hospital_patterns = [
            r"APOLLO HOSPITALS?|FORTIS|MIOT|KAUVERY|சென்னை",
            r"Ref\. No: \d+|Dated: \d{2}/\d{2}/\d{4}",
            r"Page \d+ of \d+"
        ]

    def extract_text(self, file_path):
        """Extract text from PDF or text files"""
        if file_path.lower().endswith('.pdf'):
            text = ""
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        else:  # Text file
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()

    def preprocess_text(self, text):
        """Clean text with Chennai-specific optimizations"""
        # Remove headers/footers common in Chennai hospitals
        for pattern in self.chennai_hospital_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Normalize section headers
        text = re.sub(r'\n+', '\n', text)  # Remove excessive newlines
        text = re.sub(r'\s{2,}', ' ', text)  # Remove extra spaces
        
        # Enhance Tamil-English mixed text handling
        text = re.sub(r'([a-zA-Z])([ட-ன])', r'\1 \2', text)  # Add space between English-Tamil
        text = re.sub(r'([ட-ன])([a-zA-Z])', r'\1 \2', text)  # Add space between Tamil-English
        
        return text.strip()

    def identify_sections(self, text):
        """Split report into structured sections"""
        sections = {key: "" for key in self.section_patterns}
        current_section = None
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check if line matches any section header
            for section, pattern in self.section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section
                    break
            
            # Add content to current section
            if current_section:
                sections[current_section] += line + "\n"
        
        return sections

    def parse_report(self, file_path):
        """Main function to parse medical reports"""
        try:
            # Step 1: Extract raw text
            raw_text = self.extract_text(file_path)
            
            # Step 2: Preprocess text
            cleaned_text = self.preprocess_text(raw_text)
            
            # Step 3: Identify sections
            sections = self.identify_sections(cleaned_text)
            
            # Step 4: Process sections with NLP
            results = {}
            for section, content in sections.items():
                if content.strip():
                    extracted_data = self.nlp_processor.extract_entities(content)
                    results[section] = json.loads(extracted_data)
            
            return json.dumps({
                "file": file_path,
                "sections": results
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_highlights(self, text):
        """
        Dummy implementation: returns sentences containing keywords.
        Replace with your own logic as needed.
        """
        keywords = ["critical", "urgent", "important", "alert"]
        highlights = []
        for line in text.split('\n'):
            if any(word in line.lower() for word in keywords):
                highlights.append(line.strip())
        return highlights

    def get_summary(self, text):
        """
        Generate a simple summary from the report text.
        This is a placeholder. You can improve it as needed.
        """
        # For now, just return the first 3-5 lines as a "summary"
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        summary = "\n".join(lines[:5])
        return summary

# Example usage
if __name__ == "__main__":
    parser = MedicalReportParser()
    
    # Test with sample files using robust paths
    # Assuming 'data' directory is a sibling of 'src' within the project root
    result = parser.parse_report(os.path.join(os.path.dirname(__file__), 'data', 'reports', 'sample_report.pdf'))
    print(result)
    result = parser.parse_report(os.path.join(os.path.dirname(__file__), 'data', 'reports', 'sample_report.txt'))
    print(result)