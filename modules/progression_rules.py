"""
Phase progression rule engine and clinical alert system.
Evaluates whether a patient can safely progress to the next phase.
"""

from typing import Optional
from database.db import save_alert


class ProgressionResult:
    def __init__(self):
        self.can_progress: bool = True
        self.warnings: list[str] = []
        self.blockers: list[str] = []
        self.recommendations: list[str] = []

    def block(self, reason: str) -> None:
        self.can_progress = False
        self.blockers.append(reason)

    def warn(self, reason: str) -> None:
        self.warnings.append(reason)

    def recommend(self, text: str) -> None:
        self.recommendations.append(text)


def evaluate_progression(assessment: Optional[dict], phase_key: str,
                         patient_id: int) -> ProgressionResult:
    """
    Run rule-based checks against the latest assessment.
    Returns a ProgressionResult with blockers, warnings, and recommendations.
    """
    result = ProgressionResult()

    if assessment is None:
        result.block("No assessment data available – complete an assessment first.")
        return result

    pain = assessment.get("pain_score")
    swelling = assessment.get("swelling_present", 0)
    lsi_heel = assessment.get("lsi_heel_rise")
    lsi_hop = assessment.get("lsi_single_hop")
    lsi_triple = assessment.get("lsi_triple_hop")
    lsi_cross = assessment.get("lsi_crossover_hop")
    lsi_press = assessment.get("lsi_leg_press")
    psych = assessment.get("psych_readiness")

    # ---- Universal rules ------------------------------------------------
    if pain is not None and pain > 5:
        result.block(f"Pain score is {pain}/10 – too high to progress safely.")
        _fire_alert(patient_id, assessment, f"High pain score: {pain}/10", "danger")

    if pain is not None and 3 < pain <= 5:
        result.warn(f"Pain score is {pain}/10 – monitor closely.")

    if swelling:
        result.warn("Swelling detected – recommend rest and ice before progression.")
        _fire_alert(patient_id, assessment, "Swelling present", "warning")

    # ---- Phase-specific rules -------------------------------------------
    if phase_key in ("Phase V", "Phase VI"):
        if lsi_heel is not None and lsi_heel < 80:
            result.block(f"Heel-rise LSI is {lsi_heel}% (need ≥ 80%) – not ready for running programme.")

    if phase_key == "Phase VI":
        if lsi_hop is not None and lsi_hop < 80:
            result.block(f"Single-hop LSI is {lsi_hop}% (need ≥ 80%) – defer agility drills.")
        if pain is not None and pain > 2:
            result.warn("Pain > 2/10 – return-to-run programme not advised yet.")

    # ---- Return-to-sport gate (Phase VII) --------------------------------
    if phase_key == "Phase VII":
        rts_lsis = {
            "Heel rise": lsi_heel,
            "Single hop": lsi_hop,
            "Triple hop": lsi_triple,
            "Crossover hop": lsi_cross,
            "Leg press": lsi_press,
        }
        for name, val in rts_lsis.items():
            if val is not None and val < 90:
                result.block(f"{name} LSI is {val}% (need ≥ 90% for return to sport).")

        if psych is not None and psych < 70:
            result.block(f"Psychological readiness score is {psych}% (need ≥ 70%).")

        if all(v is not None and v >= 90 for v in rts_lsis.values()):
            if psych is not None and psych >= 70:
                result.recommend("All return-to-sport criteria met – eligible for clearance evaluation.")

    # ---- Generic positive recommendations --------------------------------
    if result.can_progress and not result.warnings:
        result.recommend("Patient meets progression criteria. Consider advancing phase.")

    return result


def check_return_to_run_eligibility(assessment: Optional[dict]) -> ProgressionResult:
    """Specific check for starting the return-to-run programme."""
    result = ProgressionResult()
    if assessment is None:
        result.block("No assessment available.")
        return result

    pain = assessment.get("pain_score")
    lsi_heel = assessment.get("lsi_heel_rise")
    heel_reps = assessment.get("heel_rise_operative")
    swelling = assessment.get("swelling_present", 0)

    if pain is not None and pain > 2:
        result.block(f"Pain {pain}/10 exceeds threshold (≤ 2 required).")
    if lsi_heel is not None and lsi_heel < 80:
        result.block(f"Heel-rise LSI is {lsi_heel}% (need ≥ 80%).")
    if heel_reps is not None and heel_reps < 25:
        result.block(f"Single-leg calf raises = {heel_reps} (need ≥ 25).")
    if swelling:
        result.block("Swelling present – resolve before starting run programme.")

    if result.can_progress:
        result.recommend("Patient meets return-to-run prerequisites.")

    return result


def _fire_alert(patient_id: int, assessment: dict, message: str,
                severity: str = "warning") -> None:
    aid = assessment.get("assessment_id")
    save_alert(patient_id, message, severity, aid)
