from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.lab_fields import LabFieldCreate, LabFieldResponse

router = APIRouter(prefix="/v1", tags=["Laboratory Fields"])


@router.post("/setup/fields", response_model=LabFieldResponse)
async def create_lab_field(
    field: LabFieldCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    new_field = models.LabField(
        name=field.name, unit=field.unit, input_type=field.input_type
    )

    db.add(new_field)
    await db.commit()
    await db.refresh(new_field)

    return new_field


@router.get("/setup/fields")
async def get_all_fields(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    statement = select(models.LabField)
    result = await db.execute(statement)
    fields = result.scalars().all()
    return fields
