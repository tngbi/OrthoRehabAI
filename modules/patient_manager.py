"""
Patient management module – wraps database CRUD for the Streamlit layer.
"""

from typing import Optional
from database.db import (
    create_patient as _db_create,
    update_patient as _db_update,
    delete_patient as _db_delete,
    list_patients as _db_list,
    load_patient as _db_load,
)


def create_patient(name: str, surgery_date: str, **kwargs) -> int:
    return _db_create(name=name, surgery_date=surgery_date, **kwargs)


def update_patient(patient_id: int, **kwargs) -> None:
    _db_update(patient_id, **kwargs)


def delete_patient(patient_id: int) -> None:
    _db_delete(patient_id)


def list_patients() -> list[dict]:
    return _db_list()


def load_patient_profile(patient_id: int) -> Optional[dict]:
    return _db_load(patient_id)
