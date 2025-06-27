# setup_windows_service.py
import win32serviceutil

service_name = "ChennaiMedAI"
service_display_name = "Chennai Medical AI Assistant"
service_description = "AI assistant for Chennai healthcare providers"

win32serviceutil.InstallService(
    None,
    service_name,
    service_display_name,
    description=service_description,
    startType="auto"
)