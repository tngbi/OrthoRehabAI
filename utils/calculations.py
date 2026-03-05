"""
Clinical calculation utilities for OrthoRehabAI.
"""

from typing import Optional


def calc_lsi(operative: Optional[float], non_operative: Optional[float]) -> Optional[float]:
    """
    Limb Symmetry Index (%)  =  (operative / non_operative) × 100
    Returns None when either value is missing or non_operative is zero.
    """
    if operative is None or non_operative is None:
        return None
    if non_operative == 0:
        return None
    return round((operative / non_operative) * 100, 1)


def bmi(height_cm: Optional[float], weight_kg: Optional[float]) -> Optional[float]:
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def weeks_since(surgery_date_str: str) -> float:
    """Return weeks elapsed since surgery_date (ISO format YYYY-MM-DD)."""
    from datetime import date
    surgery = date.fromisoformat(surgery_date_str)
    delta = date.today() - surgery
    return round(delta.days / 7, 1)


def y_balance_composite(anterior: float, posteromedial: float, posterolateral: float,
                         limb_length: float) -> Optional[float]:
    """Y-Balance composite score (normalised to limb length)."""
    if limb_length == 0:
        return None
    total = anterior + posteromedial + posterolateral
    return round((total / (limb_length * 3)) * 100, 1)
