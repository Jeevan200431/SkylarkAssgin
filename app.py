import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

SHEET_ID = "1-vOcUC7a2ZkvuZdHjqI--pN627mFsQnUBm6IMCYD1z0"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# =====================================================
# GOOGLE CONNECTION (OPEN ONCE)
# =====================================================

@st.cache_resource
def get_spreadsheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json", SCOPES
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

@st.cache_data(ttl=15)
def read_sheet(name):
    sheet = get_spreadsheet().worksheet(name)
    df = pd.DataFrame(sheet.get_all_records())
    if "current_assignment" not in df.columns:
        df["current_assignment"] = ""
    return df

# =====================================================
# CLEAN DATA
# =====================================================

def clean(missions, pilots, drones):

    missions["start_date"] = pd.to_datetime(missions["start_date"], errors="coerce")
    missions["end_date"] = pd.to_datetime(missions["end_date"], errors="coerce")
    missions["mission_budget_inr"] = pd.to_numeric(missions["mission_budget_inr"], errors="coerce")
    missions["priority"] = missions["priority"].astype(str).str.strip()

    pilots["daily_rate_inr"] = pd.to_numeric(pilots["daily_rate_inr"], errors="coerce")

    drones["maintenance_due"] = pd.to_datetime(drones["maintenance_due"], errors="coerce")

    return missions, pilots, drones

# =====================================================
# CONFLICT DETECTION
# =====================================================

def overlapping(s1, e1, s2, e2):
    return max(s1, s2) <= min(e1, e2)

def double_booking(entity_id, missions, project_id, start, end):
    active = missions[missions["current_assignment"].str.contains(entity_id, na=False)]
    for _, m in active.iterrows():
        if m["project_id"] != project_id:
            if overlapping(start, end, m["start_date"], m["end_date"]):
                return True
    return False

# =====================================================
# MATCH ENGINE
# =====================================================

def mission_days(start, end):
    return (end - start).days + 1

def match(mission, pilots, drones, missions):

    results = []

    for _, pilot in pilots.iterrows():

        if pilot["status"] != "Available":
            continue
        if pilot["location"] != mission["location"]:
            continue
        if not all(cert.strip().lower() in pilot["certifications"].lower()
                   for cert in mission["required_certs"].split(",")):
            continue

        skill_score = sum(skill.strip().lower() in pilot["skills"].lower()
                          for skill in mission["required_skills"].split(","))

        if skill_score == 0:
            continue

        cost = pilot["daily_rate_inr"] * mission_days(
            mission["start_date"], mission["end_date"]
        )

        pilot_conflict = double_booking(
            pilot["pilot_id"], missions,
            mission["project_id"],
            mission["start_date"],
            mission["end_date"]
        )

        for _, drone in drones.iterrows():

            if drone["status"] != "Available":
                continue
            if drone["location"] != mission["location"]:
                continue

            weather_risk = False
            if mission["weather_forecast"].lower() == "rainy":
                if "IP43" not in drone["weather_resistance"]:
                    weather_risk = True

            maintenance_risk = False
            if pd.notna(drone["maintenance_due"]) and drone["maintenance_due"] <= mission["start_date"]:
                maintenance_risk = True

            results.append({
                "Pilot ID": pilot["pilot_id"],
                "Drone ID": drone["drone_id"],
                "Skill Score": skill_score,
                "Mission Cost (₹)": cost,
                "Budget Warning": cost > mission["mission_budget_inr"],
                "Pilot Conflict": pilot_conflict,
                "Weather Risk": weather_risk,
                "Maintenance Risk": maintenance_risk
            })

    return sorted(results, key=lambda x: (-x["Skill Score"], x["Mission Cost (₹)"]))

# =====================================================
# UPDATE ASSIGNMENT (MINIMAL CALLS)
# =====================================================

def update_assignment(project_id, pilot_id, drone_id):

    spreadsheet = get_spreadsheet()

    # -----------------------
    # Update Pilot
    # -----------------------
    pilot_sheet = spreadsheet.worksheet("pilot_roster")
    pilot_records = pilot_sheet.get_all_records()
    pilot_headers = pilot_sheet.row_values(1)

    # Ensure column exists
    if "current_assignment" not in pilot_headers:
        pilot_sheet.update_cell(1, len(pilot_headers) + 1, "current_assignment")
        pilot_headers.append("current_assignment")

    for i, row in enumerate(pilot_records):
        if row["pilot_id"] == pilot_id:
            pilot_sheet.update_cell(i + 2, pilot_headers.index("status") + 1, "Assigned")
            pilot_sheet.update_cell(i + 2, pilot_headers.index("current_assignment") + 1, project_id)
            break

    # -----------------------
    # Update Drone
    # -----------------------
    drone_sheet = spreadsheet.worksheet("drone_fleet")
    drone_records = drone_sheet.get_all_records()
    drone_headers = drone_sheet.row_values(1)

    if "current_assignment" not in drone_headers:
        drone_sheet.update_cell(1, len(drone_headers) + 1, "current_assignment")
        drone_headers.append("current_assignment")

    for i, row in enumerate(drone_records):
        if row["drone_id"] == drone_id:
            drone_sheet.update_cell(i + 2, drone_headers.index("status") + 1, "Assigned")
            drone_sheet.update_cell(i + 2, drone_headers.index("current_assignment") + 1, project_id)
            break

    # -----------------------
    # Update Mission
    # -----------------------
    mission_sheet = spreadsheet.worksheet("missions")
    mission_records = mission_sheet.get_all_records()
    mission_headers = mission_sheet.row_values(1)

    if "current_assignment" not in mission_headers:
        mission_sheet.update_cell(1, len(mission_headers) + 1, "current_assignment")
        mission_headers.append("current_assignment")

    for i, row in enumerate(mission_records):
        if row["project_id"] == project_id:
            mission_sheet.update_cell(
                i + 2,
                mission_headers.index("current_assignment") + 1,
                f"{pilot_id} | {drone_id}"
            )
            break
# =====================================================
# UI
# =====================================================

st.title("Skylark Drone Operations Coordinator AI")

menu = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Pilot Query", "Drone Query", "Match Mission", "Urgent Reassignment"]
)

missions, pilots, drones = clean(
    read_sheet("missions"),
    read_sheet("pilot_roster"),
    read_sheet("drone_fleet")
)

# ==============================
# DASHBOARD
# ==============================

if menu == "Dashboard":

    st.subheader("Active Assignments")
    st.dataframe(missions[missions["current_assignment"] != ""], use_container_width=True)

    st.subheader("Pilot Roster")
    st.dataframe(pilots, use_container_width=True)

    st.subheader("Drone Fleet")
    st.dataframe(drones, use_container_width=True)

# ==============================
# PILOT QUERY
# ==============================

elif menu == "Pilot Query":

    skill = st.text_input("Skill")
    location = st.text_input("Location")
    status = st.selectbox("Status", ["All", "Available", "Assigned", "On Leave"])

    filtered = pilots.copy()

    if skill:
        filtered = filtered[filtered["skills"].str.contains(skill, case=False, na=False)]
    if location:
        filtered = filtered[filtered["location"].str.contains(location, case=False, na=False)]
    if status != "All":
        filtered = filtered[filtered["status"] == status]

    st.dataframe(filtered, use_container_width=True)

# ==============================
# DRONE QUERY
# ==============================

elif menu == "Drone Query":

    capability = st.text_input("Capability")
    location = st.text_input("Location")
    status = st.selectbox("Status", ["All", "Available", "Assigned", "Maintenance"])

    filtered = drones.copy()

    if capability:
        filtered = filtered[filtered["capabilities"].str.contains(capability, case=False, na=False)]
    if location:
        filtered = filtered[filtered["location"].str.contains(location, case=False, na=False)]
    if status != "All":
        filtered = filtered[filtered["status"] == status]

    st.dataframe(filtered, use_container_width=True)

# ==============================
# MATCH MISSION
# ==============================

elif menu == "Match Mission":

    mission_id = st.selectbox("Select Mission", missions["project_id"])
    mission = missions[missions["project_id"] == mission_id].iloc[0]

    st.subheader("Mission Details")
    st.table(pd.DataFrame(mission).T)

    results = match(mission, pilots, drones, missions)

    if results:
        df = pd.DataFrame(results)
        st.subheader("Assignment Suggestions")
        st.dataframe(df, use_container_width=True)

        selected = st.selectbox("Select Option", df.index)

        if st.button("Confirm Assignment"):
            chosen = df.loc[selected]
            update_assignment(
                mission_id,
                chosen["Pilot ID"],
                chosen["Drone ID"]
            )
            st.success("Assignment updated.")
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("No valid options found.")

# ==============================
# URGENT
# ==============================

elif menu == "Urgent Reassignment":

    urgent = missions[missions["priority"] == "Urgent"]

    if urgent.empty:
        st.info("No urgent missions.")
    else:
        mission_id = st.selectbox("Urgent Mission", urgent["project_id"])
        mission = urgent[urgent["project_id"] == mission_id].iloc[0]

        st.table(pd.DataFrame(mission).T)

        results = match(mission, pilots, drones, missions)

        if results:
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.error("No emergency replacements available.")