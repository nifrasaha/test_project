#!/bin/bash
# WeCare AI Setup Script

echo "Installing requirements..."
pip install -r requirements.txt

echo "Downloading medical language models..."
python -m spacy download en_core_web_md
python -m spacy download en_ner_bc5cdr_md

echo "Creating database..."
sqlite3 patient_db.db "VACUUM;"

echo "Setting up environment..."
echo "ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" > .env

echo "WeCare AI is ready! Run with: streamlit run src/main.py"