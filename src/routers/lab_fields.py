from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.lab_fields import LabFieldCreate, LabFieldResponse, LabFieldUpdate

router = APIRouter(prefix="/v1", tags=["Laboratory Fields"])


@router.post("/setup/fields", response_model=LabFieldResponse)
async def create_lab_field(
    field: LabFieldCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(
            func.lower(models.LabField.name) == field.name.lower()
        )
    )

    existing_lab_field = result.scalars().first()
    if existing_lab_field is not None:
        logger.warning(f"Laboratory Field {existing_lab_field} already exists.")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_LABORATORY_FIELD_ALREADY_EXISTS",
                    "message": "Laboratory Field already exists. Please try again!",
                }
            },
        )

    new_field = models.LabField(
        name=field.name,
        unit=field.unit,
        input_type=field.input_type,
        options=field.options,
        m_min_value=field.m_min_value,
        m_max_value=field.m_max_value,
        f_min_value=field.f_min_value,
        f_max_value=field.f_max_value,
        gen_min_value=field.gen_min_value,
        gen_max_value=field.gen_max_value,
    )

    db.add(new_field)
    await db.commit()
    await db.refresh(new_field)

    return new_field


@router.patch("/setup/fields/{field_id}", response_model=LabFieldResponse)
async def update_lab_field(
    field_id: str,
    field_update: LabFieldUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # 1. Find existing field
    statement = select(models.LabField).where(models.LabField.id == field_id)
    result = await db.execute(statement)
    db_field = result.scalars().first()

    if not db_field:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_FIELD_NOT_FOUND",
                    "message": "Field not found! Please try again!",
                }
            },
        )

    # 2. Update only the fields that were provided in the request
    update_data = field_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_field, key, value)

    try:
        await db.commit()
        await db.refresh(db_field)
        return db_field
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity Error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "ERR_UPDATE_FAILED",
                    "message": "Update failed. Name might already be taken.",
                }
            },
        )


@router.get("/setup/fields")
async def get_all_fields(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    statement = select(models.LabField)
    result = await db.execute(statement)
    fields = result.scalars().all()
    return fields


@router.get("/setup/fields/{field_id}")
async def get_field(
    field_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.LabField).where(models.LabField.id == field_id)
    )
    field = result.scalar_one_or_none()
    if not field:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_FIELD_NOT_FOUND",
                    "message": "Field not found",
                }
            },
        )

    return field
