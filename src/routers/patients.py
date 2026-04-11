from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.patients import PatientCreate

router = APIRouter(prefix="/v1", tags=["Patients"])


@router.post("/patients")
async def create_patient(
    payload: PatientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(
            func.lower(models.Patient.firstName) == payload.firstName.lower(),
            func.lower(models.Patient.lastName) == payload.lastName.lower(),
        )
    )

    existing_patient = result.scalars().first()
    if existing_patient:
        logger.warning(
            f"Patient {existing_patient.firstName} {existing_patient.lastName} already exists."
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "ERR_USER_ALREADY_EXISTS",
                    "message": "Patient already exists. Please try again!",
                }
            },
        )

    now = datetime.now()

    # --- 1. Define Ranges ---
    # Yearly Range (Jan 1 to Dec 31)
    start_of_year = datetime.combine(date(now.year, 1, 1), time.min)
    end_of_year = datetime.combine(date(now.year, 12, 31), time.max)

    # Monthly Range (1st of month to last day of month)
    start_of_month = datetime.combine(date(now.year, now.month, 1), time.min)
    # To get end of month, we go to 1st of next month then minus 1 day
    next_month = now.month % 12 + 1
    year_of_next_month = now.year if now.month < 12 else now.year + 1
    end_of_month = datetime.combine(date(year_of_next_month, next_month, 1), time.min)

    # --- 2. Get the Counts ---
    # Yearly Count
    yearly_stmt = select(func.count(models.Patient.id)).where(
        models.Patient.created_at >= start_of_year,
        models.Patient.created_at <= end_of_year,
    )
    # Monthly Count
    monthly_stmt = select(func.count(models.Patient.id)).where(
        models.Patient.created_at >= start_of_month,
        models.Patient.created_at < end_of_month,
    )

    y_res = await db.execute(yearly_stmt)
    m_res = await db.execute(monthly_stmt)

    year_total = (y_res.scalar() or 0) + 1
    month_total = (m_res.scalar() or 0) + 1

    # --- 3. Format the ID ---
    year_short = now.strftime("%y")  # "26" Current Year
    month_str = now.strftime("%m")  # "04" Current Month
    m_seq = str(month_total).zfill(
        5
    )  # "00123" The Monthly Sequence (This patient is the 123rd this month).
    y_seq = str(year_total).zfill(
        5
    )  # "01500" The Yearly Sequence (This patient is the 1,500th this year).

    custom_patient_id = f"SKZ-{year_short}-{month_str}-{m_seq}-{y_seq}"
    # Result: SKZ-26-04-00123-01500

    # 4. Save to Database
    new_patient = models.Patient(**payload.model_dump(), patient_id=custom_patient_id)
    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)
    return new_patient


@router.get("/patients")
async def get_all_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    statement = select(models.Patient)
    result = await db.execute(statement)
    fields = result.scalars().all()
    return fields


@router.get("/patients/{id}")
async def get_patient(
    id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    statement = select(models.Patient).where(
        or_(models.Patient.uid == id, models.Patient.patient_id == id)
    )
    result = await db.execute(statement)
    patient = result.scalar_one_or_none()
    return patient
