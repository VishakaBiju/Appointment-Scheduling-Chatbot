# whatsapp_api.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
TEMPLATE_CONFIRM = os.getenv("WHATSAPP_TEMPLATE_CONFIRMATION", "appointment_confirmation")
BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

BASE_URL = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def send_confirmation_template(to_phone, doctor_name, date_str, time_str):
    """
    Sends a template message. This assumes a template with parameters exists in your WA Business account.
    If you don't use templates, you can instead send a plain text message.
    """
    # phone must be in international format like +919606819150
    if not to_phone.startswith("+"):
        if to_phone.startswith("0"):
            to_phone = "+91" + to_phone.lstrip("0")
        else:
            to_phone = "+91" + to_phone  # default India; adjust as needed

    # Example template payload. Modify 'components' according to your template parameters.
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": TEMPLATE_CONFIRM,
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": doctor_name},
                        {"type": "text", "text": date_str},
                        {"type": "text", "text": time_str}
                    ]
                }
            ]
        }
    }

    r = requests.post(BASE_URL, headers=HEADERS, json=payload)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"text": r.text}
    
def send_cancellation_template(to_phone, doctor_name, date_str, time_str):
    """
    Sends a WhatsApp appointment cancellation message using a pre-approved template.
    """
    if not to_phone.startswith("+"):
        if to_phone.startswith("0"):
            to_phone = "+91" + to_phone.lstrip("0")
        else:
            to_phone = "+91" + to_phone

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": os.getenv("WHATSAPP_TEMPLATE_CANCELLATION", "appointment_cancellation"),
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": doctor_name},
                        {"type": "text", "text": date_str},
                        {"type": "text", "text": time_str}
                    ]
                }
            ]
        }
    }

    r = requests.post(BASE_URL, headers=HEADERS, json=payload)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"text": r.text}
