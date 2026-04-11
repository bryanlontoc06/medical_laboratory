from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.patient_result import (
    PatientResultResponse,
    PatientResultSubmit,
    PatientResultUpdate,
)

router = APIRouter(prefix="/v1", tags=["Patients"])


@router.post("/lab/results", response_model=PatientResultResponse)
async def save_lab_results(
    payload: PatientResultSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    # 1. (Optional) Check if patient_id and template_id are valid
    patient_result = await db.execute(
        select(models.Patient).where(models.Patient.patient_id == payload.patient_id)
    )
    patient = patient_result.scalars().first()
    if not patient:
        logger.warning(f"Patient ID: {payload.patient_id} not found.")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_PATIENT_NOT_FOUND",
                    "message": f"Patient with id: {payload.patient_id} not found",
                }
            },
        )

    template_result = await db.execute(
        select(models.LabTemplate).where(
            models.LabTemplate.id == str(payload.template_id)
        )
    )
    template = template_result.scalars().first()
    if not template:
        logger.warning(f"Template ID: {payload.template_id} not found.")
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_TEMPLATE_NOT_FOUND",
                    "message": f"Template with id: {payload.template_id} not found",
                }
            },
        )

    # 2. Create the record
    new_result = models.PatientResult(
        patient_id=payload.patient_id,
        template_id=str(payload.template_id),
        result_data=payload.results,  # This is where the JSON bundle is stored
        remarks=payload.remarks,
    )

    db.add(new_result)
    await db.commit()
    await db.refresh(new_result)

    return {
        "id": new_result.id,
        "patient_id": new_result.patient_id,
        "status": "Results saved successfully",
    }


@router.patch("/lab/results/{patient_result_id}", response_model=PatientResultResponse)
async def update_patient_result(
    lab_result_id: str,
    result_update: PatientResultUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # 1. Find existing field
    statement = select(models.PatientResult).where(
        models.PatientResult.id == str(lab_result_id)
    )
    result = await db.execute(statement)
    patient_result = result.scalars().first()

    if not patient_result:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "ERR_PATIENT_RESULT_NOT_FOUND",
                    "message": "Patient Result not found! Please try again!",
                }
            },
        )

    # 2. Update only the fields that were provided in the request
    update_data = result_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(patient_result, key, value)

    try:
        await db.commit()
        await db.refresh(patient_result)
        return patient_result
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity Error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "ERR_UPDATE_FAILED",
                    "message": "Update failed.",
                }
            },
        )
