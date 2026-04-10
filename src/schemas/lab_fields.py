from enum import Enum
from typing import Optional

from pydantic import BaseModel


# This will ensure that "text", "number", or "dropdown" will be the input_type
class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"
    BOOLEAN = "boolean"


class LabFieldCreate(BaseModel):
    name: str  # e.g., "Color"
    unit: Optional[str] = None  # e.g., "mg/dL"
    input_type: FieldType = FieldType.TEXT  # default is text

    m_min_value: Optional[float] = None
    m_max_value: Optional[float] = None
    f_min_value: Optional[float] = None
    f_max_value: Optional[float] = None
    gen_min_value: Optional[float] = None
    gen_max_value: Optional[float] = None


class LabFieldResponse(LabFieldCreate):
    id: str  # UUID string

    class Config:
        orm_mode = True
