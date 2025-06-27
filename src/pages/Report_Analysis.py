import streamlit as st
from nlp_processor import MedicalNLPProcessor
import json
import pandas as pd

def main():
    st.set_page_config(page_title="Report Analysis", page_icon="📄")
    st.title("🔍 Medical Report Analysis")
    st.caption("AI-powered insights from medical documents")
    
    # Initialize processor
    processor = MedicalNLPProcessor()
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload Medical Report", 
        type=["txt", "pdf"],
        help="Supports TXT and PDF files"
    )
    
    # Text input
    manual_text = st.text_area(
        "Or enter text directly:", 
        height=200,
        placeholder="Patient presented with fever and headache..."
    )
    
    # Process input
    input_text = ""
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                input_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            except:
                st.error("PDF processing requires PyPDF2. Install with: pip install pypdf2")
        else:
            input_text = uploaded_file.getvalue().decode("utf-8")
    elif manual_text:
        input_text = manual_text
    
    # Analysis section
    if st.button("Analyze Report", type="primary") and input_text:
        with st.spinner("Analyzing medical content..."):
            results = processor.extract_entities(input_text)
            entities = json.loads(results)
            
            # Results tabs
            tab1, tab2 = st.tabs(["Structured Results", "Original Text"])
            
            with tab1:
                st.subheader("Medical Entities")
                df = pd.DataFrame(
                    [(k, len(v), ", ".join(v)) for k, v in entities.items() if v]
                )
                st.dataframe(
                    df,
                    column_config={
                        0: "Category",
                        1: "Count",
                        2: "Items"
                    },
                    hide_index=True
                )
            
            with tab2:
                st.subheader("Original Text")
                st.text_area("Full Report", value=input_text, height=400)

if __name__ == "__main__":
    main()