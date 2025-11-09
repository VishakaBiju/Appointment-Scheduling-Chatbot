import re
import uuid
from typing import Dict
from appointment_logic import (
    get_specializations, get_doctors_by_specialization, get_doctor_by_name,
    generate_next_n_days_for_doctor, get_available_time_slots, book_appointment
)
from whatsapp_api import send_confirmation_template
from appointment_logic import find_appointments_by_phone, cancel_appointment  # 👈 add these imports

# in-memory sessions
sessions: Dict[str, dict] = {}

def _new_session(user_id):
    sid = user_id or str(uuid.uuid4())
    sessions[sid] = {
        "state": "start",
        "phone": None,
        "specialization": None,
        "doctor": None,
        "date": None,
        "time": None
    }
    return sid

def _get_session(user_id):
    if user_id and user_id in sessions:
        return user_id, sessions[user_id]
    # create new
    sid = _new_session(user_id)
    return sid, sessions[sid]

def process_message(user_id, text):
    sid, sess = _get_session(user_id)
    text_clean = text.strip()
    
   # ---------------- SMALL TALK / FRIENDLY RESPONSES ----------------
    smalltalk = text_clean.lower()
 
    if any(word in smalltalk for word in ["how are you", "how r u", "how are u"]):
     return {"reply": "I'm doing great! Thanks for asking 😊 How can I help you today?","buttons": ["Book Appointment", "Cancel Appointment"]}

    elif any(word in smalltalk for word in ["thank you", "thanks", "thx", "tysm"]):
      sess["state"] = "thank_you"
      return {
        "reply": "You're most welcome! 💙 Anything else I can help you with?",
        "buttons": ["Yes", "No"]
    }

    # handle thank-you follow-up
    if sess.get("state") == "thank_you":
       if text_clean.lower() in ["yes", "y","Yes"]:
        sess["state"] = "start"
        return {
            "reply": "Sure! How can I help you today?",
            "buttons": ["Book Appointment", "Cancel Appointment", "Hospital Working Hours", "Hospital Location"]
        }
    elif text_clean.lower() in ["no", "n","No"]:
        sess["state"] = "start"
        return {
            "reply": "Alright! 😊 You can start a new conversation anytime by saying 'Hi' or 'Hello'."
        }


    elif any(word in smalltalk for word in ["bye", "goodbye", "see you"]):
     sess["state"] = "start"
     return {"reply": "Goodbye! 👋 Take care and have a great day!"
                    " You can start a new conversation anytime by saying 'Hi' or 'Hello."}

    elif any(word in smalltalk for word in ["who are you", "what are you", "what can you do"]):
     return {"reply": "I'm your hospital assistant 🤖 — I can help you book, cancel, or check appointments!"}


    # high-level quick checks
    if text_clean.lower() in ["hi", "hello", "hey", "start","good morning","good afternoon","good evening","morning","afternoon","evening"]:
        sess.update({"state": "start", "phone": None, "specialization": None, "doctor": None, "date": None, "time": None})
        return {
            "reply": "Hello! Welcome to our Hospital assistant.\nHow can I help you today?",
            "buttons": ["Book Appointment", "Cancel Appointment", "Hospital Working Hours", "Hospital Location", "Contact Help Desk"]
        }
    

    text = text.strip().lower()

    # Quick replies for basic info
    if text in ["hospital working hours", "working hours", "timing", "hours"]:
        return {
            "reply": "🕒 Our hospital is open from 9:00 AM to 5:00 PM, Monday to Friday.\n⛑️ Emergency services are available 24/7."
        }

    elif text in ["hospital location", "location", "where are you located"]:
        return {
            "reply": "📍We are located at \n#19, ITPL Main Road, near Forum Value Mall, Whitefield, Bengaluru, Karnataka – 560066."
        }

    elif text in ["contact help desk", "help desk", "contact"]:
        return {
            "reply": "☎️ Help Desk:\n📞 +91 98765 43210\n📧 support@cityhospital.com\nWe’re here to assist you 24/7!"
        }

    # ---------------- CANCEL APPOINTMENT FLOW ----------------
    if text_clean.lower() in ["cancel appointment", "cancel booking"]:
        sess["state"] = "awaiting_cancel_phone"
        return {"reply": "Please enter your registered phone number to find your bookings."}

    if sess.get("state") == "awaiting_cancel_phone":
        phone = re.sub(r'\D', '', text_clean)
        if len(phone) >= 10:
            phone = phone[-10:]
            appts = find_appointments_by_phone(phone)
            if not appts:
                sess["state"] = "start"
                return {"reply": f"No appointments found for {phone}."}

            sess["phone_for_cancel"] = phone
            sess["state"] = "awaiting_cancel_select"
            buttons = [f"{a['Doctor']} | {a['Date']} | {a['Time']}" for a in appts]
            return {
                "reply": "Select the appointment you want to cancel:",
                "buttons": buttons
            }
        else:
            return {"reply": "Please enter a valid 10-digit phone number."}

    if sess.get("state") == "awaiting_cancel_select":
        try:
            phone = sess.get("phone_for_cancel")
            doctor, date, time = [x.strip() for x in text.split('|')]
            success, msg = cancel_appointment(phone, doctor, date, time)
            #sess["state"] = "start"
            sess["phone_for_cancel"] = None

            if success:
             from whatsapp_api import send_cancellation_template
             status, wa_resp = send_cancellation_template(phone, doctor, date, time)

             print("📱 WhatsApp cancellation API response:", wa_resp)

             sess["state"] = "done"

              # Step 1: Show cancellation success message
             reply_1 = f"{msg}\n📩 Cancellation message sent on WhatsApp."

            # Step 2: Ask if user needs anything else
            reply_2 = "Anything else you’d like me to help with?"

            return {
             "reply": f"{reply_1}\n\n{reply_2}",
             "buttons": ["Book Appointment", "Hospital Working Hours", "Hospital Location"]
        }

        except Exception as e:
          sess["state"] = "done"
          return {"reply": f"Error cancelling appointment: {e}"}   
    
    # ---------------- BOOK APPOINTMENT FLOW ----------------
    state = sess.get("state", "start")

    if text_clean.lower() in ["book appointment", "book"]:
        sess["state"] = "awaiting_phone"
        return {"reply": "Sure — to start booking, please provide your phone number (10 digits).", "expect": "phone"}

    if state == "awaiting_phone":
        ph = re.sub(r'\D', '', text_clean)
        if len(ph) >= 10:
            ph = ph[-10:]
            sess["phone"] = ph
            sess["state"] = "awaiting_specialization"
            specs = get_specializations()
            return {"reply": f"✅ Phone number verified!\nStored phone → {ph}\nPlease enter the doctor's name or specialization for your appointment.", "buttons": specs}
        else:
            return {"reply": "Please enter a valid 10-digit phone number."}

    if state == "awaiting_specialization":
        chosen = text_clean
        specs = get_specializations()
        if any(chosen.strip().lower() == s.strip().lower() for s in specs):
            sess["specialization"] = chosen.strip()
            doctors = get_doctors_by_specialization(chosen.strip())
            if not doctors:
                return {"reply": f"Sorry, no doctors found for '{chosen.strip()}'. Please enter another specialization or doctor name."}
            text = f"Here are the doctors for specialization '{chosen.strip()}':\n\n"
            for d in doctors:
                text += f"🩺 {d['Doctor']} \n   🗓️ Working Days: {d.get('Days','')} \n   ⏰ Timings: {d.get('Start Time','')} - {d.get('End Time','')}\n\n"
            sess["state"] = "awaiting_doctor"
            return {"reply": text + "Please type the doctor's name from the above list to see their next 7 available days."}
        else:
            doc = get_doctor_by_name(chosen)
            if doc:
                sess["doctor"] = doc['Doctor']
                avail = generate_next_n_days_for_doctor(doc, n=7)
                text = f"Next 7 available days for {doc['Doctor']} (Working Days: {doc.get('Days','')}):\n"
                for a in avail:
                    if a['status'] == 'Available':
                        text += f"📅 {a['date']} : Available\n"
                    else:
                        text += f"📅 {a['date']} : {a['status']} - {a.get('note','')}\n"
                sess["state"] = "awaiting_date"
                return {"reply": text + "\nPlease type the date (dd-mm-yyyy) you want to book from the above list."}
            else:
                return {"reply": "I didn't find that specialization or doctor. Please pick from the provided specializations or type a correct doctor name."}

    if state == "awaiting_doctor":
        doc = get_doctor_by_name(text_clean)
        if not doc:
            return {"reply": "I couldn't find that doctor name — please type the full or partial name from the list shown."}
        sess["doctor"] = doc['Doctor']
        avail = generate_next_n_days_for_doctor(doc, n=7)
        text = f"Next 7 available days for {doc['Doctor']} (Working Days: {doc.get('Days','')}):\n\n"
        for a in avail:
           if a['status'] == 'Available':
              text += f"📅 {a['date']}: Available\n"
           else:
             text += f"📅 {a['date']}: {a['status']} - {a.get('note','')}\n"
        text += "\nPlease type the date (dd-mm-yyyy) you want to book from the above list."
        sess["state"] = "awaiting_date"
        return {"reply": text}

    if state == "awaiting_date":
        try:
            from appointment_logic import _parse_date_flexible
            date_norm = _parse_date_flexible(text_clean)
            sess["date"] = date_norm
            doc = get_doctor_by_name(sess["doctor"])
            if not doc:
                return {"reply": "Doctor not set. Please start again."}
            slots = get_available_time_slots(doc, date_norm)
            if not slots:
                sess["state"] = "awaiting_time"
                return {"reply": "No slots available on this date. Please pick another date."}
            sess["state"] = "awaiting_time"
            buttons = slots[:6]
            return {"reply": f"Available time slots for {sess['doctor']} on {date_norm}:", "buttons": buttons}
        except Exception:
            return {"reply": "Couldn't read that date. Please type the date in dd-mm or dd-mm-yyyy format."}

    if state == "awaiting_time":
        try:
            from appointment_logic import _normalize_time_string
            time_norm = _normalize_time_string(text_clean)
            sess["time"] = time_norm
        except Exception:
            return {"reply": "Couldn't parse that time. Please give time like '10', '10:00', or '10:30 AM'."}

        success, msg = book_appointment(sess['doctor'], sess['date'], sess['time'], sess['phone'])
        if success:
            status_code, wa_resp = send_confirmation_template(sess['phone'], sess['doctor'], sess['date'], sess['time'])
            sess["state"] = "done"

            print("📱 WhatsApp confirmation response:", wa_resp)  # (for backend logs)

            # Step 1: Send booking confirmation message
            reply_1 = f"{msg}\n📩 Confirmation message sent on WhatsApp."

            # Step 2: Follow-up message asking for more help
            reply_2 = "Anything else you’d like me to help with?"

            return {
               "reply": f"{reply_1}\n\n{reply_2}",
               "buttons": ["No", "Yes"]
        }
                
    if state == "done":
        if text_clean.lower() in ["no", "n"]:
            sess["state"] = "start"
            return {"reply": "Thanks — goodbye!"}
        elif text_clean.lower() in ["yes", "y"]:
            sess["state"] = "start"
            return {"reply": "Sure — how can I help you today?", "buttons": ["Book Appointment", "Cancel Appointment", "Hospital Working Hours", "Hospital Location"]}
        else:
            return {"reply": "If you need anything else type 'Book' or 'Cancel' or press a button."}
    

    # fallback
    return {"reply": "Sorry, I don't know about that. Please contact our helpline at 91-9876543210 for further assisatnce"}
