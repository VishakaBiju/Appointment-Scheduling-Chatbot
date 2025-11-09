# appointment_logic.py
from datetime import datetime, timedelta, time as dt_time
from dateutil import parser
import re

from google_sheets import (
    get_all_doctors, get_all_leaves, get_all_bookings, get_all_holidays, append_booking
)

WEEKDAY_MAP = {
    'mon': 0, 'monday': 0,
    'tue': 1, 'tues': 1, 'tuesday': 1,
    'wed': 2, 'wednesday': 2,
    'thu': 3, 'thurs': 3, 'thursday': 3,
    'fri': 4, 'friday': 4,
    'sat': 5, 'saturday': 5,
    'sun': 6, 'sunday': 6,
}

def _normalize_time_string(s):
    """
    Accept various time inputs: '10', '10am', '10:00', '10:00 AM', '10 am' -> return '10:00 AM'
    """
    s = str(s).strip()
    # try parse with dateutil to get time
    try:
        dt = parser.parse(s)
        return dt.strftime("%I:%M %p")
    except Exception:
        # fallback: if just number like '10' interpret as 10:00 AM
        m = re.match(r'^(\d{1,2})$', s)
        if m:
            hour = int(m.group(1))
            if hour >= 24:
                hour = hour % 24
            # default to AM if hour 1-11, else PM for >=12
            if hour == 0:
                hour = 12
                ampm = "AM"
            elif hour < 12:
                ampm = "AM"
            else:
                ampm = "PM"
                if hour > 12:
                    hour = hour - 12
            return f"{hour:02d}:00 {ampm}"
        raise

def _parse_date_flexible(s):
    """
    Accept dd-mm[-yyyy], dd/mm[-yyyy], or partials like 03-10 or 3/10 and return dd-mm-yyyy (YYYY current if missing)
    """
    s = s.strip()
    # replace / with -
    s2 = s.replace('/', '-')
    parts = s2.split('-')
    today = datetime.now().date()
    try:
        if len(parts) == 2:
            day = int(parts[0]); month = int(parts[1]); year = today.year
        elif len(parts) == 3:
            day = int(parts[0]); month = int(parts[1]); year = int(parts[2])
            if year < 100:  # 2-digit year
                year += 2000
        else:
            # try dateutil parse fallback
            dt = parser.parse(s2, dayfirst=True)
            return dt.strftime("%d-%m-%Y")
        dt = datetime(year, month, day)
        return dt.strftime("%d-%m-%Y")
    except Exception:
        # fallback to parser
        dt = parser.parse(s, dayfirst=True)
        return dt.strftime("%d-%m-%Y")

def get_specializations():
    doctors = get_all_doctors()
    specs = sorted(list({d['Specialization'].strip() for d in doctors if d.get('Specialization')}))
    return specs

def get_doctors_by_specialization(spec):
    doctors = get_all_doctors()
    return [d for d in doctors if d.get('Specialization') and d['Specialization'].strip().lower() == spec.strip().lower()]

def get_doctor_by_name(name):
    doctors = get_all_doctors()
    for d in doctors:
        if d.get('Doctor') and name.strip().lower() in d['Doctor'].strip().lower():
            return d
    return None

def _doctor_workdays_to_indices(workdays_str):
    # e.g. "Mon, Wed, Fri"
    parts = [p.strip().lower() for p in workdays_str.split(',')]
    idxs = []
    for p in parts:
        if p in WEEKDAY_MAP:
            idxs.append(WEEKDAY_MAP[p])
        else:
            # try first 3 letters
            p3 = p[:3]
            if p3 in WEEKDAY_MAP:
                idxs.append(WEEKDAY_MAP[p3])
    return sorted(set(idxs))

def is_holiday(date_str):
    """date_str must be dd-mm-yyyy"""
    holidays = get_all_holidays()
    for h in holidays:
        d = h.get('Date')
        if not d: continue
        try:
            # normalize both
            from dateutil import parser
            if parser.parse(d, dayfirst=True).strftime("%d-%m-%Y") == date_str:
                return True, h.get('Occasion') or ""
        except Exception:
            continue
    return False, ""

def is_doctor_on_leave(doctor_name, date_str):
    leaves = get_all_leaves()
    for l in leaves:
        if l.get('Doctor') and l.get('Date'):
            try:
                if l['Doctor'].strip().lower() == doctor_name.strip().lower():
                    from dateutil import parser
                    if parser.parse(l['Date'], dayfirst=True).strftime("%d-%m-%Y") == date_str:
                        return True, l.get('Reason') or ""
            except Exception:
                continue
    return False, ""

def generate_next_n_days_for_doctor(doctor_record, n=7):
    # returns list of dicts {date_str, available(boolean), reason_if_not}
    workdays = _doctor_workdays_to_indices(doctor_record.get('Days', ''))
    results = []
    today = datetime.now().date()
    days_checked = 0
    day = today
    while len(results) < n:
        weekday_idx = day.weekday()
        readable = day.strftime("%d-%m-%Y")
        if weekday_idx in workdays:
            # check holiday and leave
            hol, hol_name = is_holiday(readable)
            if hol:
                results.append({'date': readable, 'status': 'Holiday', 'note': hol_name})
                day = day + timedelta(days=1); continue
            leave, leave_reason = is_doctor_on_leave(doctor_record['Doctor'], readable)
            if leave:
                results.append({'date': readable, 'status': 'Leave', 'note': leave_reason})
                day = day + timedelta(days=1); continue
            # else available
            results.append({'date': readable, 'status': 'Available', 'note': ''})
        day = day + timedelta(days=1)
        days_checked += 1
        if days_checked > 30:  # fallback safety
            break
    return results

def get_available_time_slots(doctor_record, date_str, slot_minutes=20):
    """
    Returns available times like ["03:00 PM", "03:20 PM", ...] excluding booked times for given doctor/date.
    """

    # --- Fix: normalize time strings properly ---
    def normalize_time(time_str):
        t = str(time_str).strip().upper().replace('.', '').replace(' ', '')
        # Ensure AM/PM present
        if 'AM' not in t and 'PM' not in t:
            # Guess based on hour
            hour = int(t.split(':')[0]) if ':' in t else int(re.sub(r'\D', '', t) or 9)
            t += 'PM' if hour >= 12 else 'AM'
        # Handle 12 PM / 12 AM edge cases properly
        if t.startswith("12:") and "AM" in t:
            return parser.parse("00:" + t.split(':', 1)[1])
        elif t.startswith("12:") and "PM" in t:
            return parser.parse("12:" + t.split(':', 1)[1])
        return parser.parse(t)

    # --- Parse doctor start and end times ---
    try:
        st = normalize_time(doctor_record['Start Time'])
        ed = normalize_time(doctor_record['End Time'])
    except Exception as e:
        print(f"[WARN] Time parse failed for {doctor_record.get('Doctor')} → {e}")
        st = parser.parse("09:00 AM")
        ed = parser.parse("05:00 PM")

    print(f"[DEBUG] {doctor_record['Doctor']} slots from {st.strftime('%I:%M %p')} to {ed.strftime('%I:%M %p')}")

    # --- Generate slot list ---
    slots = []
    cur = st
    while cur < ed:
        slots.append(cur.strftime("%I:%M %p"))
        cur = cur + timedelta(minutes=slot_minutes)

    # --- Remove booked slots ---
    bookings = get_all_bookings()
    booked = [
        b['Time']
        for b in bookings
        if b.get('Doctor')
        and b.get('Date')
        and b['Doctor'].strip().lower() == doctor_record['Doctor'].strip().lower()
        and _parse_date_flexible(b['Date']) == date_str
    ]

    available = [s for s in slots if s not in booked]
    return available


def book_appointment(doctor_name, date_raw, time_raw, phone):
    """
    Accepts flexible date/time, normalizes then appends to sheet.
    returns (success, message)
    """
    date_str = _parse_date_flexible(date_raw)  # dd-mm-yyyy
    try:
        time_norm = _normalize_time_string(time_raw)
    except Exception as e:
        return False, f"Couldn't parse time: {e}"

    # check doctor exists
    dr = get_doctor_by_name(doctor_name)
    if not dr:
        return False, "Doctor not found."

    # check holiday / leave
    hol, holname = is_holiday(date_str)
    if hol:
        return False, f"Selected date is a holiday ({holname})."
    leave, leavereason = is_doctor_on_leave(dr['Doctor'], date_str)
    if leave:
        return False, f"Doctor is on leave ({leavereason})."

    # check if slot available
    available = get_available_time_slots(dr, date_str)
    if time_norm not in available:
        # suggest next available time if any
        if available:
            return False, f"Selected time is not available. Next available: {available[0]}"
        else:
            return False, "No available slots on this date."

    # All good -> append
    append_booking(dr['Doctor'], date_str, time_norm, phone)
    return True, f"Appointment with {dr['Doctor']} on {date_str} at {time_norm} booked."

def find_appointments_by_phone(phone):
    """
    Find all bookings for a given phone number.
    Returns a list of dicts: [{'Doctor':..., 'Date':..., 'Time':...}]
    """
    bookings = get_all_bookings()
    results = []
    for b in bookings:
        if str(b.get('Phone', '')).strip() == str(phone).strip():
            results.append({
                'Doctor': b.get('Doctor', ''),
                'Date': b.get('Date', ''),
                'Time': b.get('Time', '')
            })
    return results


def cancel_appointment(phone, doctor, date, time):
    """
    Remove a booking entry that matches phone, doctor, date, and time.
    Returns (success, message)
    """
    from google_sheets import get_all_bookings, overwrite_bookings
    from dateutil import parser

    def normalize_date(d):
        try:
            return parser.parse(d, dayfirst=True).strftime("%d-%m-%Y")
        except Exception:
            return d.strip()

    def normalize_time(t):
        try:
            return parser.parse(t).strftime("%I:%M %p")
        except Exception:
            return str(t).strip().upper().replace('.', '').replace('  ', ' ')

    target_date = normalize_date(date)
    target_time = normalize_time(time)
    target_doctor = doctor.strip().lower()
    target_phone = str(phone).strip()

    bookings = get_all_bookings()
    new_data = []
    found = False

    for b in bookings:
        b_date = normalize_date(b.get('Date', ''))
        b_time = normalize_time(b.get('Time', ''))
        b_doctor = b.get('Doctor', '').strip().lower()
        b_phone = str(b.get('Phone', '')).strip()

        if (
            b_phone == target_phone
            and b_doctor == target_doctor
            and b_date == target_date
            and b_time == target_time
        ):
            found = True
            continue  # skip (this cancels)
        new_data.append(b)

    if not found:
        # Debug help
        print(f"[DEBUG] Cancel not found → looking for {target_doctor} | {target_date} | {target_time} | {target_phone}")
        return False, "No matching appointment found."

    overwrite_bookings(new_data)
    return True, f" Appointment with {doctor} on {target_date} at {target_time} has been cancelled."
    
    # 🚀 Send WhatsApp cancellation message
    print(f"📨 Sending WhatsApp cancellation to {phone}...")
    status, resp = send_cancellation_template(phone, doctor, target_date, target_time)
    print("📱 WhatsApp API response:", status, resp)

    # Return chatbot message
    return True, f"Appointment with {doctor} on {target_date} at {target_time} has been cancelled."

  #  # Overwrite Google Sheet with updated list (without the cancelled one)
  ##  from google_sheets import overwrite_bookings
   # overwrite_bookings(new_data)
   # return True, f"Appointment with {doctor} on {date} at {time} has been cancelled."
