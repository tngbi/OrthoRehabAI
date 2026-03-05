"""
Assessment engine – processes functional assessment data,
computes LSIs, and persists results.
"""

from typing import Optional
from utils.calculations import calc_lsi
from database.db import save_assessment, get_assessments, get_latest_assessment


def compute_lsis(data: dict) -> dict:
    """
    Given raw assessment data, compute all Limb Symmetry Index values
    and return updated data dict ready for storage.
    """
    lsi_pairs = [
        ("lsi_heel_rise",     "heel_rise_operative",     "heel_rise_non_operative"),
        ("lsi_single_hop",    "single_hop_operative",    "single_hop_non_operative"),
        ("lsi_triple_hop",    "triple_hop_operative",    "triple_hop_non_operative"),
        ("lsi_crossover_hop", "crossover_hop_operative", "crossover_hop_non_operative"),
        ("lsi_vertical_jump", "vertical_jump_operative", "vertical_jump_non_operative"),
        ("lsi_leg_press",     "leg_press_1rm_operative", "leg_press_1rm_non_operative"),
    ]

    for lsi_key, op_key, non_op_key in lsi_pairs:
        data[lsi_key] = calc_lsi(data.get(op_key), data.get(non_op_key))

    # Y-balance composite LSI
    y_op = [data.get("y_balance_anterior_op"),
            data.get("y_balance_pm_op"),
            data.get("y_balance_pl_op")]
    y_non = [data.get("y_balance_anterior_non"),
             data.get("y_balance_pm_non"),
             data.get("y_balance_pl_non")]

    if all(v is not None for v in y_op) and all(v is not None for v in y_non):
        op_total = sum(y_op)
        non_total = sum(y_non)
        data["lsi_y_balance"] = calc_lsi(op_total, non_total)
    else:
        data["lsi_y_balance"] = None

    return data


def store_assessment(data: dict) -> int:
    data = compute_lsis(data)
    return save_assessment(data)


def fetch_assessments(patient_id: int) -> list[dict]:
    return get_assessments(patient_id)


def fetch_latest_assessment(patient_id: int) -> Optional[dict]:
    return get_latest_assessment(patient_id)
