from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from src import models


async def get_template_structure_recursive(
    template_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    structure_list: list[dict[str, Any]] = []

    # Get all components of this template, sorted by sort_order
    stmt = (
        select(models.TemplateStructure)
        .where(models.TemplateStructure.parent_id == template_id)
        .order_by(models.TemplateStructure.sort_order)
    )

    result = await db.execute(stmt)
    components = result.scalars().all()

    for item in components:
        # Use getattr to get the actual value, not the Column object
        f_id = getattr(item, "field_id")
        c_id = getattr(item, "child_template_id")

        # SCENARIO A: If a FIELD is found
        if f_id is not None:
            field_stmt = select(models.LabField).where(
                models.LabField.id == item.field_id
            )
            field_result = await db.execute(field_stmt)
            field = field_result.scalar_one_or_none()

            if field:
                raw_field_data: dict[str, Any] = {
                    "type": "field",
                    "field_id": field.id,
                    "name": field.name,
                    "input_type": field.input_type,
                    "unit": field.unit,
                    "m_max_value": field.m_max_value,
                    "m_min_value": field.m_min_value,
                    "f_max_value": field.f_max_value,
                    "f_min_value": field.f_min_value,
                    "gen_max_value": field.gen_max_value,
                    "gen_min_value": field.gen_min_value,
                    "options": field.options,
                }

                filtered_field = {
                    k: v for k, v in raw_field_data.items() if v is not None and v != 0
                }

                structure_list.append(filtered_field)

        # SCENARIO B: If another TEMPLATE (Sub-test/Package) is found
        elif c_id is not None:
            template_stmt = select(models.LabTemplate).where(
                models.LabTemplate.id == item.child_template_id
            )
            template_result = await db.execute(template_stmt)
            child_template = template_result.scalar_one_or_none()

            if child_template:
                # RECURSION: Function calls itself to dig deeper into the package
                child_structure = await get_template_structure_recursive(
                    str(child_template.id), db
                )

                structure_list.append(
                    {
                        "type": "sub_template",
                        "template_id": child_template.id,
                        "name": child_template.name,
                        "fields": child_structure,  # This is the nested result
                    }
                )

    return structure_list
