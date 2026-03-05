"""
PDF clinical report generator using ReportLab.
"""

import io
import os
from datetime import date
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

from modules.phase_engine import get_rehabilitation_phase, get_phase_details
from modules.assessment_engine import fetch_latest_assessment, fetch_assessments
from modules.progression_rules import evaluate_progression


def generate_report(patient: dict) -> bytes:
    """Generate a full clinical PDF report and return bytes."""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            leftMargin=15 * mm, rightMargin=15 * mm)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Heading2"],
                              textColor=colors.HexColor("#2c3e50"),
                              spaceAfter=6))
    styles.add(ParagraphStyle("SmallBody", parent=styles["BodyText"], fontSize=9))

    elements: list = []

    # ── Title ────────────────────────────────────────────────────────
    elements.append(Paragraph("OrthoRehabAI – Clinical Report", styles["Title"]))
    elements.append(Paragraph("Achilles Tendon Repair Rehabilitation", styles["Heading3"]))
    elements.append(Spacer(1, 6 * mm))

    # ── Patient info ─────────────────────────────────────────────────
    phase_info = get_rehabilitation_phase(patient["surgery_date"])
    phase_detail = get_phase_details(phase_info["phase_key"])

    patient_data = [
        ["Name", patient["name"], "Patient ID", str(patient["patient_id"])],
        ["Age", str(patient.get("age", "—")), "Gender", patient.get("gender", "—")],
        ["Surgery Date", patient["surgery_date"], "Surgeon", patient.get("surgeon") or "—"],
        ["Injury", patient.get("injury_type", "—"), "Weeks Post-Op", str(phase_info["weeks_since_surgery"])],
        ["Current Phase", phase_info["phase_name"], "Week Range", phase_info["week_range"]],
    ]

    t = Table(patient_data, colWidths=[35 * mm, 55 * mm, 35 * mm, 55 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecf0f1")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#ecf0f1")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6 * mm))

    # ── Phase goals & restrictions ───────────────────────────────────
    elements.append(Paragraph("Phase Goals", styles["SectionTitle"]))
    for g in phase_detail.get("goals", []):
        elements.append(Paragraph(f"• {g}", styles["SmallBody"]))
    elements.append(Spacer(1, 3 * mm))

    elements.append(Paragraph("Restrictions", styles["SectionTitle"]))
    for r in phase_detail.get("restrictions", []):
        elements.append(Paragraph(f"• {r}", styles["SmallBody"]))
    elements.append(Spacer(1, 6 * mm))

    # ── Assessment scores ────────────────────────────────────────────
    latest = fetch_latest_assessment(patient["patient_id"])
    if latest:
        elements.append(Paragraph("Latest Assessment", styles["SectionTitle"]))
        assess_data = [
            ["Metric", "Operative", "Non-operative", "LSI (%)"],
            ["Heel Rise (reps)",
             str(latest.get("heel_rise_operative", "—")),
             str(latest.get("heel_rise_non_operative", "—")),
             _fmt(latest.get("lsi_heel_rise"))],
            ["Single Hop (cm)",
             str(latest.get("single_hop_operative", "—")),
             str(latest.get("single_hop_non_operative", "—")),
             _fmt(latest.get("lsi_single_hop"))],
            ["Triple Hop (cm)",
             str(latest.get("triple_hop_operative", "—")),
             str(latest.get("triple_hop_non_operative", "—")),
             _fmt(latest.get("lsi_triple_hop"))],
            ["Crossover Hop (cm)",
             str(latest.get("crossover_hop_operative", "—")),
             str(latest.get("crossover_hop_non_operative", "—")),
             _fmt(latest.get("lsi_crossover_hop"))],
            ["Vertical Jump (cm)",
             str(latest.get("vertical_jump_operative", "—")),
             str(latest.get("vertical_jump_non_operative", "—")),
             _fmt(latest.get("lsi_vertical_jump"))],
            ["Leg Press 1RM (kg)",
             str(latest.get("leg_press_1rm_operative", "—")),
             str(latest.get("leg_press_1rm_non_operative", "—")),
             _fmt(latest.get("lsi_leg_press"))],
            ["Pain Score", str(latest.get("pain_score", "—")), "", ""],
            ["Psych Readiness", f"{latest.get('psych_readiness', '—')}%", "", ""],
        ]
        at = Table(assess_data, colWidths=[45 * mm, 35 * mm, 40 * mm, 30 * mm])
        at.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(at)
        elements.append(Spacer(1, 6 * mm))

    # ── Progression evaluation ───────────────────────────────────────
    result = evaluate_progression(latest, phase_info["phase_key"], patient["patient_id"])
    elements.append(Paragraph("Progression Evaluation", styles["SectionTitle"]))
    if result.blockers:
        for b in result.blockers:
            elements.append(Paragraph(f"🛑 BLOCKED: {b}", styles["SmallBody"]))
    if result.warnings:
        for w in result.warnings:
            elements.append(Paragraph(f"⚠ WARNING: {w}", styles["SmallBody"]))
    for rec in result.recommendations:
        elements.append(Paragraph(f"✓ {rec}", styles["SmallBody"]))

    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width="100%", color=colors.grey))
    elements.append(Spacer(1, 4 * mm))

    # ── Disclaimer ───────────────────────────────────────────────────
    elements.append(Paragraph(
        "<i>Disclaimer: This report is generated by OrthoRehabAI as a clinical decision "
        "support tool. It does not replace professional medical advice. "
        "Always consult the treating physician.</i>",
        styles["SmallBody"]
    ))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"<i>Report generated: {date.today().isoformat()}</i>",
        styles["SmallBody"]
    ))

    doc.build(elements)
    return buf.getvalue()


def _fmt(val: Optional[float]) -> str:
    return f"{val}%" if val is not None else "—"
