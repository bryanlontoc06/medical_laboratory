from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PatientResultSubmit(BaseModel):
    patient_id: str
    template_id: UUID
    # 'results' can be a list of objects with nested data
    # or a simplified dictionary of values.
    # For flexibility, we will use Dict[str, Any]
    results: Dict[str, Any]
    remarks: Optional[str] = None


class PatientResultResponse(BaseModel):
    id: UUID
    status: str
