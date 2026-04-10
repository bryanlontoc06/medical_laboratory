from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.templates import LabTemplateCreate, LabTemplateResponse

router = APIRouter(prefix="/v1", tags=["Laboratory Templates"])


@router.post("/setup/templates", response_model=LabTemplateResponse)
async def create_template(
    data: LabTemplateCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Create the main Template record first
    new_template = models.LabTemplate(name=data.name, is_package=data.is_package)
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    # 2. Save the components into the TemplateStructure table
    for item in data.structure:
        struct_entry = models.TemplateStructure(
            parent_id=new_template.id,
            field_id=str(item.field_id) if item.field_id else None,
            child_template_id=str(item.child_template_id)
            if item.child_template_id
            else None,
            sort_order=item.sort_order,
        )
        db.add(struct_entry)

    await db.commit()
    return new_template
