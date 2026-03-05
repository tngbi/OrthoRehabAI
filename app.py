import streamlit as st
from datetime import date
from logic.phase_engine import get_phase
from protocol.phases import PHASE_CONTENT

st.set_page_config(page_title="Achilles Rehab Assistant", layout="wide")

st.title("🏥 Achilles Tendon Rehabilitation Assistant")

st.sidebar.header("Patient Profile")

name = st.sidebar.text_input("Patient Name")
surgery_date = st.sidebar.date_input("Surgery Date")

if surgery_date:
    phase = get_phase(surgery_date)

    st.header("Current Rehabilitation Phase")
    st.success(phase)

    content = PHASE_CONTENT.get(phase, {})

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Goals")
        for g in content.get("goals", []):
            st.write("•", g)

    with col2:
        st.subheader("Weight Bearing")
        for w in content.get("weight_bearing", []):
            st.write("•", w)

    st.subheader("Exercises")
    for e in content.get("exercises", []):
        st.write("•", e)

    st.subheader("Progression Criteria")
    for c in content.get("criteria", []):
        st.write("•", c)

else:
    st.info("Enter a surgery date to calculate rehabilitation phase.")

st.divider()

st.caption(
    "Disclaimer: This tool assists clinicians but does not replace medical advice. "
    "Always consult the treating surgeon or physiotherapist."
)