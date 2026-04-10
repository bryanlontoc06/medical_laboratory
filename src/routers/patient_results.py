from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.schemas.patient_result import PatientResultResponse, PatientResultSubmit

router = APIRouter(prefix="/v1", tags=["Patient Results"])


@router.post("/lab/results", response_model=PatientResultResponse)
async def save_lab_results(
    payload: PatientResultSubmit,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    # 1. (Optional) Check if patient_id and template_id are valid

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
        "patien_id": new_result.patient_id,
        "status": "Results saved successfully",
    }
