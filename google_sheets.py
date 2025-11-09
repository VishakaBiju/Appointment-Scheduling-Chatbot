# google_sheets.py
import os
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

CREDS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
DOCTOR_SHEET_ID = os.getenv("DOCTOR_SHEET_ID")
HOLIDAY_SHEET_ID = os.getenv("HOLIDAY_SHEET_ID")
FAQ_SHEET_ID = os.getenv("FAQ_SHEET_ID")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]

_creds = Credentials.from_service_account_file(CREDS_PATH, scopes=SCOPES)
_client = gspread.authorize(_creds)

# Doctors database contains multiple worksheets: "Sheet1" (doctors), "leave", "slot"
_doctor_db = _client.open_by_key(DOCTOR_SHEET_ID)
doctors_sheet = _doctor_db.worksheet("Sheet1")   # doctor list
leaves_sheet = _doctor_db.worksheet("leave")     # leaves
slots_sheet = _doctor_db.worksheet("slot")       # bookings (append here)

holiday_sheet = _client.open_by_key(HOLIDAY_SHEET_ID).sheet1
faq_sheet = _client.open_by_key(FAQ_SHEET_ID).sheet1

# Helper: get all records
def get_all_doctors():
    return doctors_sheet.get_all_records()

def get_all_leaves():
    return leaves_sheet.get_all_records()

def get_all_bookings():
    return slots_sheet.get_all_records()

def get_all_holidays():
    return holiday_sheet.get_all_records()

def get_all_faq():
    return faq_sheet.get_all_records()

def append_booking(doctor, date_str, time_str, phone):
    """
    append row to slots_sheet in order: Doctor, Date, Time, Phone
    """
    slots_sheet.append_row([doctor, date_str, time_str, phone])
    return True

def overwrite_bookings(all_bookings):
    """
    Replace all rows in the bookings sheet.
    """
    sheet = slots_sheet
    sheet.clear()
    sheet.append_row(["Doctor", "Date", "Time", "Phone"])  # header
    for b in all_bookings:
        sheet.append_row([b['Doctor'], b['Date'], b['Time'], b['Phone']])
