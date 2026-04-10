from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TemplateStructureSchema(BaseModel):
    # You can pass a Field ID..
    field_id: Optional[UUID] = Field(
        default=None, examples=[None, "3fa85f64-5717-4562-b3fc-2c963f66afa6"]
    )
    # ...or a Child Template ID (if this is a package)
    child_template_id: Optional[UUID] = Field(
        default=None, examples=[None, "3fa85f64-5717-4562-b3fc-2c963f66afa6"]
    )
    sort_order: int = 0


class LabTemplateCreate(BaseModel):
    name: str  # e.g., "Urinalysis" or "Pregnancy Package"
    is_package: bool = False
    # List of fields or sub-templates to be included
    structure: List[TemplateStructureSchema]


class LabTemplateResponse(BaseModel):
    id: UUID
    name: str
    is_package: bool

    model_config = ConfigDict(from_attributes=True)
