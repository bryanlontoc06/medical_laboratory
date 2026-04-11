from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# This will ensure that "text", "number", "dropdown" or "checklist" will be the input_type
class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DROPDOWN = "dropdown"
    BOOLEAN = "boolean"
    CHECKLIST = "checklist"


class LabFieldCreate(BaseModel):
    name: str  # e.g., "Color"
    unit: Optional[str] = Field(
        None, json_schema_extra={"example": "mg/dL"}
    )  # e.g., "mg/dL"
    input_type: FieldType = Field(
        default=FieldType.TEXT, json_schema_extra={"example": "number"}
    )  # default is text

    m_min_value: Optional[float] = Field(None, json_schema_extra={"example": 70.0})
    m_max_value: Optional[float] = Field(None, json_schema_extra={"example": 100.0})
    f_min_value: Optional[float] = Field(None, json_schema_extra={"example": 70.0})
    f_max_value: Optional[float] = Field(None, json_schema_extra={"example": 100.0})
    gen_min_value: Optional[float] = None
    gen_max_value: Optional[float] = None

    options: Optional[List[str]] = Field(
        None, json_schema_extra={"example": ["Sugar", "Pregnancy Test", "Albumin"]}
    )


class LabFieldResponse(LabFieldCreate):
    id: str  # UUID string

    model_config = ConfigDict(from_attributes=True)


class LabFieldUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    input_type: Optional[FieldType] = None
    options: Optional[List[str]] = None
    m_min_value: Optional[float] = None
    m_max_value: Optional[float] = None
    f_min_value: Optional[float] = None
    f_max_value: Optional[float] = None
    gen_min_value: Optional[float] = None
    gen_max_value: Optional[float] = None
