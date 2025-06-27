from typing import Self
import streamlit as st
import os
import hashlib
from cryptography.fernet import Fernet

# Load encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY not set in environment")

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def authenticate():
    """Professional authentication system"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("WeCare Secure Login")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image("secure_login.png", width=150)
            
        with col2:
            username = st.text_input("Medical ID")
            password = st.text_input("Password", type="password")
            if st.button("Access Medical Portal"):
                if Self._verify_credentials(username, password):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        st.stop()

def _verify_credentials(username, password):
    """Validate against hashed credentials (demo version)"""
    # In production: Connect to your user database
    valid_users = {
        "doctor@chennaimc.in": hashlib.sha256("ChennaiMed2024".encode()).hexdigest(),
        "clinic@adyar.in": hashlib.sha256("AdyarClinic!123".encode()).hexdigest()
    }
    return valid_users.get(username) == hashlib.sha256(password.encode()).hexdigest()