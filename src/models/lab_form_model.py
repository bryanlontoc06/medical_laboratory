import uuid

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db.database import Base

LAB_TEMPLATES_TABLE = "lab_templates"
LAB_FIELDS_TABLE = "lab_fields"


def generate_uuid():
    return str(uuid.uuid4())


# TABLE 1: Library of Fields (e.g., Color, pH, Sugar)
class LabField(Base):
    __tablename__ = LAB_FIELDS_TABLE
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)  # e.g., "mg/dL"
    input_type = Column(
        String(50), default="text"
    )  # e.g., "text", "number", "dropdown"
    # Male Reference Range
    m_min_value = Column(Float(10), nullable=True)
    m_max_value = Column(Float(10), nullable=True)

    # Female Reference Range
    f_min_value = Column(Float(10), nullable=True)
    f_max_value = Column(Float(10), nullable=True)

    # General Reference Range (Optional: applicable to all patients regardless of gender)
    gen_min_value = Column(Float(10), nullable=True)
    gen_max_value = Column(Float(10), nullable=True)


# TABLE 2: Library of Templates/Packages (e.g., Urinalysis, Buntis Package)
class LabTemplate(Base):
    __tablename__ = LAB_TEMPLATES_TABLE
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    is_package = Column(
        Boolean, default=False
    )  # Set to 'True' if this represents a bundle of other tests

    # Relationship to fetch the structure
    structure = relationship(
        "TemplateStructure",
        back_populates="parent",
        foreign_keys="TemplateStructure.parent_id",
    )


# TABLE 3: Linker - Handles hierarchical/nesting logic
class TemplateStructure(Base):
    __tablename__ = "template_structure"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_id = Column(String(36), ForeignKey(f"{LAB_TEMPLATES_TABLE}.id"))

    # Link an individual Field...
    field_id = Column(String(36), ForeignKey(f"{LAB_FIELDS_TABLE}.id"), nullable=True)

    # ...or another Template (for nested Packages)
    child_template_id = Column(
        String(36), ForeignKey(f"{LAB_TEMPLATES_TABLE}.id"), nullable=True
    )

    sort_order = Column(Integer, default=0)

    parent = relationship(
        "LabTemplate", foreign_keys=[parent_id], back_populates="structure"
    )


# TABLE 4: Actual Patient Results
class PatientResult(Base):
    __tablename__ = "patient_results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), nullable=False)
    template_id = Column(String(36), ForeignKey(f"{LAB_TEMPLATES_TABLE}.id"))
    # JSONB format for flexible data entry by the admin
    result_data = Column(JSON, nullable=False)
