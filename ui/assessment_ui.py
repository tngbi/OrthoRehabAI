"""
Assessment UI – functional assessment form and progress charts.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date

from modules.phase_engine import get_rehabilitation_phase
from modules.assessment_engine import store_assessment, fetch_assessments, fetch_latest_assessment
from modules.progression_rules import check_return_to_run_eligibility


def render_assessment_form(patient: dict) -> None:
    """Render the digital functional assessment form."""

    phase_info = get_rehabilitation_phase(patient["surgery_date"])

    st.subheader("Functional Assessment")
    st.caption(f"Phase: {phase_info['phase_name']}  |  Weeks post-op: {phase_info['weeks_since_surgery']}")

    with st.form("assessment_form"):
        st.markdown("#### Range of Motion")
        rom1, rom2, rom3, rom4 = st.columns(4)
        df_op = rom1.number_input("DF Operative (°)", value=0.0, step=1.0, key="df_op")
        df_non = rom2.number_input("DF Non-operative (°)", value=0.0, step=1.0, key="df_non")
        pf_op = rom3.number_input("PF Operative (°)", value=0.0, step=1.0, key="pf_op")
        pf_non = rom4.number_input("PF Non-operative (°)", value=0.0, step=1.0, key="pf_non")

        st.markdown("#### Pain & Swelling")
        pc1, pc2 = st.columns(2)
        pain = pc1.slider("Pain Score (0–10)", 0, 10, 0, key="pain")
        swelling = pc2.selectbox("Swelling Present?", [("No", 0), ("Yes", 1)],
                                  format_func=lambda x: x[0], key="swell")

        st.markdown("#### Standing Heel Rise Test (reps)")
        hr1, hr2 = st.columns(2)
        hr_op = hr1.number_input("Operative", value=0, min_value=0, key="hr_op")
        hr_non = hr2.number_input("Non-operative", value=0, min_value=0, key="hr_non")

        st.markdown("#### Hop Tests (cm)")
        h1, h2 = st.columns(2)
        sh_op = h1.number_input("Single Hop – Op", value=0.0, min_value=0.0, key="sh_op")
        sh_non = h2.number_input("Single Hop – Non-op", value=0.0, min_value=0.0, key="sh_non")
        th_op = h1.number_input("Triple Hop – Op", value=0.0, min_value=0.0, key="th_op")
        th_non = h2.number_input("Triple Hop – Non-op", value=0.0, min_value=0.0, key="th_non")
        ch_op = h1.number_input("Crossover Hop – Op", value=0.0, min_value=0.0, key="ch_op")
        ch_non = h2.number_input("Crossover Hop – Non-op", value=0.0, min_value=0.0, key="ch_non")

        st.markdown("#### Vertical Jump (cm)")
        vj1, vj2 = st.columns(2)
        vj_op = vj1.number_input("Operative", value=0.0, min_value=0.0, key="vj_op")
        vj_non = vj2.number_input("Non-operative", value=0.0, min_value=0.0, key="vj_non")

        st.markdown("#### Y-Balance Test (cm)")
        yb1, yb2 = st.columns(2)
        ya_op = yb1.number_input("Anterior – Op", value=0.0, key="ya_op")
        ya_non = yb2.number_input("Anterior – Non-op", value=0.0, key="ya_non")
        ypm_op = yb1.number_input("Posteromedial – Op", value=0.0, key="ypm_op")
        ypm_non = yb2.number_input("Posteromedial – Non-op", value=0.0, key="ypm_non")
        ypl_op = yb1.number_input("Posterolateral – Op", value=0.0, key="ypl_op")
        ypl_non = yb2.number_input("Posterolateral – Non-op", value=0.0, key="ypl_non")

        st.markdown("#### Strength – Single-Leg Press 1RM (kg)")
        lp1, lp2 = st.columns(2)
        lp_op = lp1.number_input("Operative", value=0.0, min_value=0.0, key="lp_op")
        lp_non = lp2.number_input("Non-operative", value=0.0, min_value=0.0, key="lp_non")

        st.markdown("#### Psychological Readiness")
        psych = st.slider("Return-to-Sport Readiness (0–100%)", 0, 100, 50, key="psych")

        st.markdown("#### Clinician Notes")
        clinician_notes = st.text_area("Notes", key="clin_notes")

        submitted = st.form_submit_button("Save Assessment", type="primary")

    if submitted:
        data = {
            "patient_id": patient["patient_id"],
            "assessment_date": date.today().isoformat(),
            "weeks_post_op": phase_info["weeks_since_surgery"],
            "phase": phase_info["phase_key"],
            "df_operative": df_op,
            "df_non_operative": df_non,
            "pf_operative": pf_op,
            "pf_non_operative": pf_non,
            "pain_score": pain,
            "swelling_present": swelling[1],
            "heel_rise_operative": hr_op,
            "heel_rise_non_operative": hr_non,
            "single_hop_operative": sh_op,
            "single_hop_non_operative": sh_non,
            "triple_hop_operative": th_op,
            "triple_hop_non_operative": th_non,
            "crossover_hop_operative": ch_op,
            "crossover_hop_non_operative": ch_non,
            "vertical_jump_operative": vj_op,
            "vertical_jump_non_operative": vj_non,
            "y_balance_anterior_op": ya_op,
            "y_balance_anterior_non": ya_non,
            "y_balance_pm_op": ypm_op,
            "y_balance_pm_non": ypm_non,
            "y_balance_pl_op": ypl_op,
            "y_balance_pl_non": ypl_non,
            "leg_press_1rm_operative": lp_op,
            "leg_press_1rm_non_operative": lp_non,
            "psych_readiness": psych,
            "clinician_notes": clinician_notes.strip() or None,
        }
        aid = store_assessment(data)
        st.success(f"Assessment saved (ID: {aid}).")
        st.rerun()


# ── LSI Results Display ─────────────────────────────────────────────────

def render_lsi_results(patient: dict) -> None:
    """Display the latest LSI results with a radar chart."""

    latest = fetch_latest_assessment(patient["patient_id"])
    if latest is None:
        st.info("No assessments recorded yet.")
        return

    st.subheader("Limb Symmetry Index – Latest")

    lsi_labels = {
        "lsi_heel_rise": "Heel Rise",
        "lsi_single_hop": "Single Hop",
        "lsi_triple_hop": "Triple Hop",
        "lsi_crossover_hop": "Crossover Hop",
        "lsi_vertical_jump": "Vertical Jump",
        "lsi_y_balance": "Y-Balance",
        "lsi_leg_press": "Leg Press 1RM",
    }

    values = []
    labels = []
    for key, label in lsi_labels.items():
        v = latest.get(key)
        if v is not None:
            labels.append(label)
            values.append(v)

    if not values:
        st.info("No LSI data available in the latest assessment.")
        return

    # Table
    cols = st.columns(len(values))
    for i, (label, val) in enumerate(zip(labels, values)):
        delta_colour = "normal" if val >= 90 else ("off" if val >= 80 else "inverse")
        cols[i].metric(label, f"{val}%", delta=f"{'✓' if val >= 90 else '↓'}", delta_color=delta_colour)

    # Radar chart
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="Operative LSI",
        line_color="#3498db",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[90] * (len(labels) + 1),
        theta=labels + [labels[0]],
        name="90% Target",
        line=dict(dash="dash", color="#e74c3c"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 120])),
        showlegend=True,
        height=400,
        margin=dict(t=30, b=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Return-to-run eligibility
    st.divider()
    st.subheader("Return-to-Run Eligibility")
    rtr = check_return_to_run_eligibility(latest)
    if rtr.can_progress:
        for r in rtr.recommendations:
            st.success(r)
    else:
        for b in rtr.blockers:
            st.error(b)


# ── Progress Charts ─────────────────────────────────────────────────────

def render_progress_charts(patient: dict) -> None:
    """Longitudinal progress charts using all stored assessments."""

    assessments = fetch_assessments(patient["patient_id"])
    if not assessments:
        st.info("No assessments recorded yet — complete at least one to see progress charts.")
        return

    df = pd.DataFrame(assessments)
    df["assessment_date"] = pd.to_datetime(df["assessment_date"])

    st.subheader("Progress Over Time")

    # Pain trend
    if "pain_score" in df.columns and df["pain_score"].notna().any():
        fig_pain = px.line(df, x="assessment_date", y="pain_score",
                           markers=True, title="Pain Score Trend")
        fig_pain.add_hline(y=5, line_dash="dash", line_color="red",
                           annotation_text="Progression block threshold")
        fig_pain.update_yaxes(range=[0, 10])
        st.plotly_chart(fig_pain, use_container_width=True)

    # Heel rise
    if "heel_rise_operative" in df.columns and df["heel_rise_operative"].notna().any():
        fig_hr = go.Figure()
        fig_hr.add_trace(go.Scatter(x=df["assessment_date"], y=df["heel_rise_operative"],
                                    mode="lines+markers", name="Operative"))
        fig_hr.add_trace(go.Scatter(x=df["assessment_date"], y=df["heel_rise_non_operative"],
                                    mode="lines+markers", name="Non-operative"))
        fig_hr.update_layout(title="Standing Heel Rise (reps)", yaxis_title="Reps")
        st.plotly_chart(fig_hr, use_container_width=True)

    # LSI progression
    lsi_cols = [c for c in df.columns if c.startswith("lsi_") and df[c].notna().any()]
    if lsi_cols:
        fig_lsi = go.Figure()
        for col in lsi_cols:
            fig_lsi.add_trace(go.Scatter(
                x=df["assessment_date"], y=df[col],
                mode="lines+markers", name=col.replace("lsi_", "").replace("_", " ").title()
            ))
        fig_lsi.add_hline(y=90, line_dash="dash", line_color="green",
                          annotation_text="RTS target (90%)")
        fig_lsi.add_hline(y=80, line_dash="dot", line_color="orange",
                          annotation_text="Run programme (80%)")
        fig_lsi.update_layout(title="LSI Progression (%)", yaxis_title="LSI %",
                              yaxis_range=[0, 120])
        st.plotly_chart(fig_lsi, use_container_width=True)

    # Leg press strength
    if "leg_press_1rm_operative" in df.columns and df["leg_press_1rm_operative"].notna().any():
        fig_lp = go.Figure()
        fig_lp.add_trace(go.Scatter(x=df["assessment_date"], y=df["leg_press_1rm_operative"],
                                    mode="lines+markers", name="Operative"))
        fig_lp.add_trace(go.Scatter(x=df["assessment_date"], y=df["leg_press_1rm_non_operative"],
                                    mode="lines+markers", name="Non-operative"))
        fig_lp.update_layout(title="Single-Leg Press 1RM (kg)", yaxis_title="kg")
        st.plotly_chart(fig_lp, use_container_width=True)
