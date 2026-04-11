from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class PatientCreate(BaseModel):
    firstName: str = Field(
        min_length=1,
        max_length=100,
        examples=["Juan"],
    )
    lastName: str = Field(
        min_length=1,
        max_length=100,
        examples=["Dela Cruz"],
    )
    gender: GenderEnum = Field(
        ...,  # required
        description="Biological sex of the patient for laboratory reference ranges",
        examples=["Male", "Female"],
    )
    address: Optional[str] = Field(
        min_length=1, max_length=255, default=None, examples=[None]
    )
    age_value: Optional[int] = Field(None, ge=0, examples=[20, 5])
    age_unit: Optional[str] = Field(
        default="years", examples=["years", "months", "days"]
    )
    requested_by: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        examples=[None, "Dr. John Doe"],
    )
