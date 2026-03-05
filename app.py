"""
OrthoRehabAI – Clinical Rehabilitation Intelligence Platform
Main Streamlit application entry point.
"""

import streamlit as st
import pandas as pd

from database.db import init_db
from modules.patient_manager import list_patients, load_patient_profile
from modules.phase_engine import (
    get_rehabilitation_phase,
    get_phase_details,
    get_return_to_run_programme,
    get_agility_plyometrics,
)
from modules.assessment_engine import fetch_latest_assessment
from modules.progression_rules import check_return_to_run_eligibility

from ui.dashboard import render_dashboard
from ui.patient_ui import render_patient_registration, render_patient_list, render_patient_edit
from ui.assessment_ui import render_assessment_form, render_lsi_results, render_progress_charts
from reports.pdf_generator import generate_report

# ── Page configuration ──────────────────────────────────────────────────
st.set_page_config(
    page_title="OrthoRehabAI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialise database ─────────────────────────────────────────────────
init_db()

# ── Custom CSS for professional medical UI ──────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] {background-color: #f7f9fc;}
    .block-container {padding-top: 1.5rem;}
    h1 {color: #2c3e50;}
    .stMetric label {font-size: 0.85rem !important;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/color/96/physical-therapy.png", width=64)
st.sidebar.title("OrthoRehabAI")
st.sidebar.caption("Clinical Rehabilitation Intelligence Platform")

# Patient selector
patients = list_patients()
patient_options = {p["patient_id"]: p["name"] for p in patients}

if patient_options:
    selected_id = st.sidebar.selectbox(
        "Select Patient",
        options=list(patient_options.keys()),
        format_func=lambda x: patient_options[x],
    )
else:
    selected_id = None
    st.sidebar.info("No patients registered. Use the Patients tab to add one.")

# Navigation
nav = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Patients", "Assessment", "Running Programme",
     "Agility & Plyometrics", "Progress", "Reports"],
    index=0,
)

st.sidebar.divider()
st.sidebar.caption(
    "⚕️ **Disclaimer:** This tool assists clinicians but does not replace "
    "professional medical advice. Always consult the treating physician."
)

# ── Load selected patient ───────────────────────────────────────────────
patient = load_patient_profile(selected_id) if selected_id else None


# ═════════════════════════════════════════════════════════════════════════
#  TAB ROUTING
# ═════════════════════════════════════════════════════════════════════════

if nav == "Dashboard":
    st.title("🏥 Clinical Dashboard")
    if patient:
        render_dashboard(patient)
    else:
        st.info("Select or register a patient to view the dashboard.")

# ── Patients ─────────────────────────────────────────────────────────────
elif nav == "Patients":
    st.title("👤 Patient Management")
    tab_reg, tab_list, tab_edit = st.tabs(["Register", "Patient List", "Edit Patient"])
    with tab_reg:
        render_patient_registration()
    with tab_list:
        render_patient_list()
    with tab_edit:
        if patient:
            render_patient_edit(patient)
        else:
            st.info("Select a patient from the sidebar to edit.")

# ── Assessment ───────────────────────────────────────────────────────────
elif nav == "Assessment":
    st.title("📋 Functional Assessment")
    if patient:
        tab_form, tab_lsi = st.tabs(["New Assessment", "LSI Results"])
        with tab_form:
            render_assessment_form(patient)
        with tab_lsi:
            render_lsi_results(patient)
    else:
        st.info("Select a patient first.")

# ── Running Programme ────────────────────────────────────────────────────
elif nav == "Running Programme":
    st.title("🏃 Return-to-Run Programme")

    if patient:
        # Eligibility check
        latest = fetch_latest_assessment(patient["patient_id"])
        elig = check_return_to_run_eligibility(latest)

        if not elig.can_progress:
            st.warning("**Patient does not yet meet return-to-run prerequisites:**")
            for b in elig.blockers:
                st.error(b)
            st.divider()
            st.caption("The programme is shown for reference but should NOT be started yet.")
        else:
            st.success("Patient meets return-to-run prerequisites.")

        prog = get_return_to_run_programme()

        st.subheader("Prerequisites")
        for p in prog.get("prerequisites", []):
            st.markdown(f"- {p}")

        st.divider()
        st.subheader("Phase 1 – Walk / Jog Intervals")
        p1_data = []
        for w in prog.get("phase_1_walk_jog", []):
            p1_data.append({
                "Week": w["week"],
                "Programme": w["description"],
                "Sessions / Week": w["sessions_per_week"],
                "Total Time (min)": (w["walk_min"] + w["jog_min"]) * w["repetitions"],
            })
        st.table(pd.DataFrame(p1_data))

        st.subheader("Phase 2 – Progressive Running")
        p2_data = []
        for w in prog.get("phase_2_running", []):
            p2_data.append({
                "Week": w["week"],
                "Programme": w["description"],
                "Duration (min)": w["duration_min"],
                "Sessions / Week": w["sessions_per_week"],
            })
        st.table(pd.DataFrame(p2_data))
    else:
        st.info("Select a patient first.")

# ── Agility & Plyometrics ───────────────────────────────────────────────
elif nav == "Agility & Plyometrics":
    st.title("⚡ Agility & Plyometric Training")

    ap = get_agility_plyometrics()

    # Phase 1 – Agility
    agility = ap.get("phase_1_agility", {})
    st.subheader(agility.get("title", "Agility Drills"))
    st.markdown("**Prerequisites:**")
    for p in agility.get("prerequisites", []):
        st.markdown(f"- {p}")

    st.markdown("**Drills:**")
    for d in agility.get("drills", []):
        desc = f"**{d['name']}** – {d['sets']} sets"
        if "distance_m" in d:
            desc += f" × {d['distance_m']}m"
        if "rest_sec" in d:
            desc += f" (rest {d['rest_sec']}s)"
        st.markdown(f"- {desc}")

    st.divider()

    # Phase 2 – Plyometrics
    plyo = ap.get("phase_2_plyometrics", {})
    st.subheader(plyo.get("title", "Plyometric Training"))
    st.markdown("**Prerequisites:**")
    for p in plyo.get("prerequisites", []):
        st.markdown(f"- {p}")

    st.markdown("**Drills:**")
    for d in plyo.get("drills", []):
        desc = f"**{d['name']}** – {d['sets']} sets"
        if "reps" in d:
            desc += f" × {d['reps']} reps"
        if "distance_m" in d:
            desc += f" × {d['distance_m']}m"
        st.markdown(f"- {desc}")

# ── Progress ─────────────────────────────────────────────────────────────
elif nav == "Progress":
    st.title("📈 Patient Progress Tracking")
    if patient:
        render_progress_charts(patient)
    else:
        st.info("Select a patient first.")

# ── Reports ──────────────────────────────────────────────────────────────
elif nav == "Reports":
    st.title("📄 Clinical Report")
    if patient:
        st.write(f"Generate a PDF report for **{patient['name']}**.")
        if st.button("Generate PDF Report", type="primary"):
            with st.spinner("Generating report..."):
                pdf_bytes = generate_report(patient)
            st.download_button(
                label="⬇️ Download Report",
                data=pdf_bytes,
                file_name=f"OrthoRehabAI_Report_{patient['name'].replace(' ', '_')}.pdf",
                mime="application/pdf",
            )
            st.success("Report generated successfully.")
    else:
        st.info("Select a patient first.")