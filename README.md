# Skylark Drone Operations Coordinator AI Agent

An AI-powered operations coordination system built to manage pilots, drones, and missions efficiently using Google Sheets as a live backend.

This project was developed as part of a technical assignment to simulate the responsibilities of a Drone Operations Coordinator.

---
### LIVE DEMO  
URL : https://jeevandroneoperations.streamlit.app/  


##  Problem Overview

Skylark Drones operates multiple pilots and drones across different client missions simultaneously. Manual coordination leads to:

- Scheduling conflicts
- Skill mismatches
- Equipment issues
- Budget overruns
- High operational overhead

This AI agent automates and optimizes those processes.

---

##  Core Features Implemented

### 1️ Roster Management
- Query pilots by skill, location, and status
- Calculate mission cost based on pilot daily rate
- View current assignments
- Update pilot status (2-way Google Sheets sync)

### 2️ Assignment Tracking
- Match pilots based on:
  - Skills
  - Certifications
  - Location
  - Availability
- Match drones based on:
  - Weather compatibility
  - Location
  - Availability
- Confirm assignment with sheet update
- Track active assignments

### 3️ Drone Inventory
- Query drones by capability and location
- Filter by availability
- Weather resistance validation
- Maintenance risk flagging
- Deployment tracking

### 4️ Conflict Detection
- Double booking detection (overlapping mission dates)
- Certification mismatch prevention
- Budget overrun warning
- Weather risk alerts
- Maintenance risk alerts
- Location mismatch filtering

### 5️ Urgent Reassignment
- Identifies missions marked as `Urgent`
- Re-runs matching engine for emergency replacement
- Supports quick reassignment decisions

---

##  Architecture Overview

Frontend:
- Streamlit (interactive UI)

Backend:
- Google Sheets (live database)
- gspread API for read/write operations

Data Flow:
- Read data from Google Sheets
- Apply matching + validation logic
- Display recommendations
- Write assignment updates back to sheets

---

##  Google Sheets Integration

2-way synchronization:

- Reads:
  - pilot_roster
  - drone_fleet
  - missions

- Writes:
  - Pilot status
  - Drone status
  - Mission current_assignment

---

##  Technologies Used

- Python
- Streamlit
- Pandas
- gspread
- Google Sheets API
- OAuth2 Service Account Authentication

---

##  How To Run Locally

1. Clone repository:git clone https://github.com/Jeevan200431/SkylarkAssgin  
cd droneoperations

2. Create virtual environment:

python -m venv venv


3. Activate environment:

venv\Scripts\activate


4. Install dependencies:

pip install -r requirements.txt


5. Add your Google service account credentials:
- Place `service_account.json` in root directory
- Share your Google Sheet with service account email

6. Run:

streamlit run app.py


---

##  Deployment

The application can be deployed using:

- Streamlit Community Cloud (recommended)
- Render
- Railway

Google credentials should be stored securely using environment secrets.

---

##  Key Design Decisions

- Used Google Sheets for simplicity and live collaboration
- Implemented caching to reduce API quota issues
- Designed modular matching engine for scalability
- Used rule-based validation for explainability
- Prioritized clarity over black-box AI

---

##  Future Improvements

- Role-based access control
- Advanced scheduling optimization
- Automated budget optimization engine
- Real-time weather API integration
- LLM-powered natural language query interface

---

##  Author

Developed by: **Jeevan MR**

---

##  License

This project was built for educational and evaluation purposes.
