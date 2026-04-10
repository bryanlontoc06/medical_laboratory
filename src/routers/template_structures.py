from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models
from src.routers.utils import get_template_structure_recursive

router = APIRouter(prefix="/v1", tags=["Laboratory Template Structures"])


@router.get("/test-forms/{template_id}")
async def get_form_definition(
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    result = await db.execute(
        select(models.LabTemplate).where(models.LabTemplate.id == template_id)
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

    # 2. Get the recursive structure
    form_structure = await get_template_structure_recursive(template_id, db)

    return {
        "template_id": template.id,
        "template_name": template.name,
        "is_package": template.is_package,
        "structure": form_structure,
    }
