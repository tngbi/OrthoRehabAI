"""
Dashboard UI – main clinical overview for the selected patient.
"""

import streamlit as st
import plotly.graph_objects as go

from modules.phase_engine import get_rehabilitation_phase, get_phase_details
from modules.assessment_engine import fetch_latest_assessment
from modules.progression_rules import evaluate_progression
from database.db import get_active_alerts


# ── Phase colour mapping ────────────────────────────────────────────────
_PHASE_COLOURS = {
    "Phase I": "#e74c3c",
    "Phase II": "#e67e22",
    "Phase III": "#f1c40f",
    "Phase IV": "#2ecc71",
    "Phase V": "#1abc9c",
    "Phase VI": "#3498db",
    "Phase VII": "#9b59b6",
}


def render_dashboard(patient: dict) -> None:
    """Render the main clinical dashboard for a selected patient."""

    surgery_date = patient["surgery_date"]
    phase_info = get_rehabilitation_phase(surgery_date)
    phase_key = phase_info["phase_key"]
    phase_detail = get_phase_details(phase_key)
    latest = fetch_latest_assessment(patient["patient_id"])
    colour = _PHASE_COLOURS.get(phase_key, "#34495e")

    # ── Header metrics ──────────────────────────────────────────────
    st.markdown(f"### {patient['name']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Surgery Date", surgery_date)
    c2.metric("Weeks Post-Op", phase_info["weeks_since_surgery"])
    c3.metric("Current Phase", phase_key)
    c4.metric("Week Range", phase_info["week_range"])

    st.markdown(
        f"<div style='background:{colour};color:#fff;padding:12px 18px;"
        f"border-radius:8px;font-size:1.15rem;margin-bottom:16px'>"
        f"<b>{phase_detail.get('phase_name', phase_key)}</b></div>",
        unsafe_allow_html=True,
    )

    # ── Alerts ──────────────────────────────────────────────────────
    alerts = get_active_alerts(patient["patient_id"])
    if alerts:
        for a in alerts:
            if a["severity"] == "danger":
                st.error(f"🚨 {a['message']}")
            else:
                st.warning(f"⚠️ {a['message']}")

    # ── Phase detail sections ───────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Goals")
        for g in phase_detail.get("goals", []):
            st.markdown(f"- {g}")

        st.subheader("Weight Bearing")
        st.info(phase_detail.get("weight_bearing_status", "—"))

        st.subheader("Restrictions")
        for r in phase_detail.get("restrictions", []):
            st.markdown(f"- {r}")

    with col_right:
        st.subheader("Exercises")
        tabs = st.tabs(["Mobility", "Strengthening", "Balance", "Cardio"])
        with tabs[0]:
            for e in phase_detail.get("mobility_exercises", []):
                st.markdown(f"- {e}")
        with tabs[1]:
            for e in phase_detail.get("strengthening_exercises", []):
                st.markdown(f"- {e}")
        with tabs[2]:
            for e in phase_detail.get("balance_training", []):
                st.markdown(f"- {e}")
            if not phase_detail.get("balance_training"):
                st.caption("Not applicable in this phase.")
        with tabs[3]:
            for e in phase_detail.get("cardio_training", []):
                st.markdown(f"- {e}")

    # ── Progression criteria & evaluation ───────────────────────────
    st.divider()
    st.subheader("Progression Criteria")
    for c in phase_detail.get("progression_criteria", []):
        st.markdown(f"✅ {c}")

    result = evaluate_progression(latest, phase_key, patient["patient_id"])

    if result.blockers:
        st.error("**Phase progression BLOCKED**")
        for b in result.blockers:
            st.markdown(f"🛑 {b}")
    if result.warnings:
        for w in result.warnings:
            st.warning(w)
    for rec in result.recommendations:
        st.success(rec)

    # ── Phase timeline gauge ────────────────────────────────────────
    st.divider()
    st.subheader("Rehabilitation Timeline")
    _render_phase_gauge(phase_info["weeks_since_surgery"])


def _render_phase_gauge(weeks: float) -> None:
    labels = ["I", "II", "III", "IV", "V", "VI", "VII"]
    boundaries = [0, 3, 6, 8, 10, 12, 24, 52]

    fig = go.Figure()

    for i, label in enumerate(labels):
        fig.add_trace(go.Bar(
            x=[boundaries[i + 1] - boundaries[i]],
            y=["Phase"],
            orientation="h",
            name=f"Phase {label}",
            marker_color=list(_PHASE_COLOURS.values())[i],
            text=label,
            textposition="inside",
            hovertemplate=f"Phase {label}: week {boundaries[i]}–{boundaries[i+1]}<extra></extra>",
        ))

    fig.add_vline(x=min(weeks, 52), line_width=3, line_dash="dash", line_color="black",
                  annotation_text=f"Week {weeks}", annotation_position="top")
    fig.update_layout(
        barmode="stack",
        height=120,
        margin=dict(l=0, r=0, t=30, b=0),
        showlegend=False,
        xaxis_title="Weeks",
        yaxis_visible=False,
    )
    st.plotly_chart(fig, use_container_width=True)
