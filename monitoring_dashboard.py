# Real-time monitoring for Chennai hospitals
import streamlit as st
import psutil

def system_monitor():
    st.title("Chennai AI Health Monitor")
    
    # System health
    col1, col2, col3 = st.columns(3)
    col1.metric("CPU", f"{psutil.cpu_percent()}%")
    col2.metric("Memory", f"{psutil.virtual_memory().percent}%")
    col3.metric("Active Users", "24", "+8 today")
    
    # Usage analytics
    st.subheader("Chennai Hospital Usage")
    hospitals = ["Apollo", "Kauvery", "MIOT", "GH Chennai"]
    usage = [120, 85, 67, 42]
    st.bar_chart(dict(zip(hospitals, usage)))
    
    # Error logs
    st.subheader("System Logs")
    with open("error_log.txt", "r") as f:
        st.code(f.read())