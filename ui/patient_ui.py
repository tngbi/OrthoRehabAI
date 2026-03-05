"""
Patient management UI – registration, editing, listing.
"""

import streamlit as st
from datetime import date
from modules.patient_manager import (
    create_patient,
    update_patient,
    delete_patient,
    list_patients,
    load_patient_profile,
)


def render_patient_registration() -> None:
    """Render the patient registration / editing form."""

    st.subheader("Register New Patient")

    with st.form("patient_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *")
            age = st.number_input("Age", min_value=0, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            height_cm = st.number_input("Height (cm)", min_value=0.0, value=170.0, step=0.1)
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, value=70.0, step=0.1)
        with col2:
            surgery_date = st.date_input("Surgery Date *", value=date.today())
            surgeon = st.text_input("Surgeon")
            injury_type = st.text_input("Injury Type", value="Achilles Tendon Repair")
            comorbidities = st.text_area("Comorbidities")
            notes = st.text_area("Notes")

        submitted = st.form_submit_button("Register Patient", type="primary")

    if submitted:
        if not name.strip():
            st.error("Patient name is required.")
            return
        pid = create_patient(
            name=name.strip(),
            surgery_date=surgery_date.isoformat(),
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            surgeon=surgeon.strip() or None,
            injury_type=injury_type.strip(),
            comorbidities=comorbidities.strip() or None,
            notes=notes.strip() or None,
        )
        st.success(f"Patient **{name}** registered (ID: {pid}).")
        st.rerun()


def render_patient_list() -> None:
    """Show all patients in a table with edit/delete actions."""

    st.subheader("Patient List")
    patients = list_patients()

    if not patients:
        st.info("No patients registered yet.")
        return

    for p in patients:
        with st.expander(f"{p['name']}  —  Surgery: {p['surgery_date']}"):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Age:** {p['age']}  |  **Gender:** {p['gender']}")
                st.write(f"**Height:** {p['height_cm']} cm  |  **Weight:** {p['weight_kg']} kg")
                st.write(f"**Surgeon:** {p['surgeon'] or '—'}")
            with col2:
                st.write(f"**Injury:** {p['injury_type']}")
                st.write(f"**Comorbidities:** {p['comorbidities'] or '—'}")
                st.write(f"**Notes:** {p['notes'] or '—'}")
            with col3:
                if st.button("Delete", key=f"del_{p['patient_id']}"):
                    delete_patient(p["patient_id"])
                    st.success(f"Deleted {p['name']}.")
                    st.rerun()


def render_patient_edit(patient: dict) -> None:
    """Edit form for the currently selected patient."""

    st.subheader(f"Edit Patient – {patient['name']}")

    with st.form("edit_patient_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=patient["name"])
            age = st.number_input("Age", value=patient["age"] or 30, min_value=0)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                  index=["Male", "Female", "Other"].index(patient.get("gender", "Male")))
            height_cm = st.number_input("Height (cm)", value=float(patient.get("height_cm") or 170))
            weight_kg = st.number_input("Weight (kg)", value=float(patient.get("weight_kg") or 70))
        with col2:
            surgery_date = st.date_input("Surgery Date",
                                         value=date.fromisoformat(patient["surgery_date"]))
            surgeon = st.text_input("Surgeon", value=patient.get("surgeon") or "")
            injury_type = st.text_input("Injury Type", value=patient.get("injury_type", ""))
            comorbidities = st.text_area("Comorbidities", value=patient.get("comorbidities") or "")
            notes = st.text_area("Notes", value=patient.get("notes") or "")

        saved = st.form_submit_button("Save Changes", type="primary")

    if saved:
        update_patient(
            patient["patient_id"],
            name=name.strip(),
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            surgery_date=surgery_date.isoformat(),
            surgeon=surgeon.strip() or None,
            injury_type=injury_type.strip(),
            comorbidities=comorbidities.strip() or None,
            notes=notes.strip() or None,
        )
        st.success("Patient updated.")
        st.rerun()
