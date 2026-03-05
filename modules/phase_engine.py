"""
Rehabilitation phase engine.
Determines current phase from surgery date using protocol week ranges.
"""

from datetime import date
from typing import Tuple
import json
import os

_PROTOCOL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "protocol.json"
)

_protocol_cache: dict | None = None


def _load_protocol() -> dict:
    global _protocol_cache
    if _protocol_cache is None:
        with open(_PROTOCOL_PATH, "r", encoding="utf-8") as f:
            _protocol_cache = json.load(f)
    return _protocol_cache


def load_protocol() -> dict:
    """Public access to full protocol data."""
    return _load_protocol()


def get_rehabilitation_phase(surgery_date: str | date) -> dict:
    """
    Return the current rehabilitation phase based on weeks since surgery.

    Parameters
    ----------
    surgery_date : str (YYYY-MM-DD) or datetime.date

    Returns
    -------
    dict with keys: phase_key, phase_name, weeks_since_surgery, week_range
    """
    if isinstance(surgery_date, str):
        surgery_date = date.fromisoformat(surgery_date)

    delta_days = (date.today() - surgery_date).days
    weeks = round(delta_days / 7, 1)

    protocol = _load_protocol()
    phases = protocol["phases"]

    matched_key = "Phase VII"  # default fallback
    for key, phase in phases.items():
        if phases[key]["week_start"] <= weeks <= phases[key]["week_end"]:
            matched_key = key
            break

    phase_data = phases[matched_key]
    return {
        "phase_key": matched_key,
        "phase_name": phase_data["phase_name"],
        "weeks_since_surgery": weeks,
        "week_range": phase_data["week_range"],
    }


def get_phase_details(phase_key: str) -> dict:
    """Return the full protocol detail dict for a given phase key."""
    protocol = _load_protocol()
    return protocol["phases"].get(phase_key, {})


def get_return_to_run_programme() -> dict:
    return _load_protocol().get("return_to_run_programme", {})


def get_agility_plyometrics() -> dict:
    return _load_protocol().get("agility_and_plyometrics", {})
