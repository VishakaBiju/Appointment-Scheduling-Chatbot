# Appointment-Scheduling-Chatbot


An intelligent chatbot system designed to automate **hospital appointment scheduling** using a conversational interface.  
It allows users to book, cancel, and manage appointments, ask about hospital hours and location, and receive **real-time WhatsApp confirmations**.

---

# Project Overview
This chatbot simplifies hospital interactions by combining:
- A **web-based frontend** (HTML, CSS, JavaScript)
- A **Flask backend** (Python)
- Integration with the **Meta WhatsApp Cloud API**
- **Google Sheets** as the appointment database

The system ensures an interactive, easy-to-use interface for patients and a scalable backend for hospitals.

---

# Features

| Functionality | Description |
|----------------|-------------|
|  Interactive Chat | Users can chat naturally with the bot using buttons or text. |
|  Appointment Booking | Book appointments by choosing doctor, date, and time. |
|  Appointment Cancellation | Cancel an existing appointment with instant feedback. |
|  Hospital Info | Provides working hours, contact, and location details. |
|  WhatsApp Integration | Sends confirmation/cancellation messages automatically. |
|  Chat Persistence | Chat history stored in browser localStorage until cleared. |

---

# System Architecture

**Frontend:**  
- Built using HTML, CSS, and JavaScript  
- Interactive chat interface (`index.html`, `style.css`, `script.js`)  
- Uses localStorage for saving chat history  

**Backend:**  
- Developed in Flask (`app.py`, `chatbotlogic.py`, `appointment_logic.py`)  
- Handles chatbot logic, session management, and WhatsApp API integration  

**Database:**  
- Uses a connected Google Sheet to store appointment data  
- Google Sheet includes columns for Doctor, Date, Time, and Phone number  

**WhatsApp API Integration:**  
- Sends automated confirmation and cancellation templates via the **Meta Cloud API**  
- Requires an access token, phone number ID, and approved message templates  

---

# Tools & Technologies

| Component | Technology |
|------------|-------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python (Flask) |
| Database | Google Sheets |
| API | Meta WhatsApp Cloud API |
| Libraries | `requests`, `flask`, `dotenv` |
| IDE | Visual Studio Code |
| Browser | Google Chrome |

---

# Future Scope
- Host chatbot publicly using Render, Heroku, or GitHub Pages.  
- Expand functionality with RAG (Retrieval-Augmented Generation) for dynamic FAQ answers.  
- Add authentication for patients and doctors.  
- Enhance analytics with Power BI integration using Google Sheets data.

---

# Screenshots (Optional)
You can include screenshots of:
- Chatbot interface  
- WhatsApp confirmation messages  
- Google Sheet structure  

---

#Author
Vishaka Biju  


---

