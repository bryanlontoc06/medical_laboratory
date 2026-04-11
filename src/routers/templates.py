from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.templates import LabTemplateCreate, LabTemplateResponse

router = APIRouter(prefix="/v1", tags=["Laboratory Templates"])


@router.post("/setup/templates", response_model=LabTemplateResponse)
async def create_template(
    data: LabTemplateCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.LabTemplate).where(
            func.lower(models.LabTemplate.name) == data.name.lower()
        )
    )

    existing_lab_template = result.scalars().first()
    if existing_lab_template is not None:
        logger.warning(f"Laboratory Template {existing_lab_template} already exists.")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_LABORATORY_TEMPLATE_ALREADY_EXISTS",
                    "message": "Laboratory Template already exists. Please try again!",
                }
            },
        )

    # 1. Create the main Template record first
    new_template = models.LabTemplate(name=data.name, is_package=data.is_package)
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    # 2. Save the components into the TemplateStructure table
    if data.structure:
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


@router.patch("/setup/templates/{template_id}", response_model=LabTemplateResponse)
async def update_template(
    template_id: str,
    data: LabTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # 1. Find existing template
    result = await db.execute(
        select(models.LabTemplate).where(models.LabTemplate.id == str(template_id))
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_TEMPLATE_NOT_FOUND",
                    "message": "Template not found",
                }
            },
        )

    # 2. Update basic info
    setattr(template, "name", data.name)
    setattr(template, "is_package", data.is_package)

    # 3. The Sync Strategy
    if data.structure is not None:
        from sqlalchemy import delete

        await db.execute(
            delete(models.TemplateStructure).where(
                models.TemplateStructure.parent_id == template_id
            )
        )

        await db.flush()

        for item in data.structure:
            new_struct = models.TemplateStructure(
                parent_id=template.id,
                field_id=str(item.field_id) if item.field_id else None,
                child_template_id=str(item.child_template_id)
                if item.child_template_id
                else None,
                sort_order=item.sort_order,
            )
            db.add(new_struct)

    await db.commit()
    await db.refresh(template)
    return template
