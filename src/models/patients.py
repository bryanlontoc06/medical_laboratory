import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class GenderEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, default=generate_uuid
    )
    patient_id: Mapped[str] = mapped_column(String(100), unique=True)
    firstName: Mapped[str] = mapped_column(String(100), nullable=False)
    lastName: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    age_value: Mapped[int] = mapped_column(Integer, nullable=True)
    age_unit: Mapped[str] = mapped_column(
        String(20), nullable=True
    )  # "years", "months", "days"
    requested_by: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("firstName", "lastName", name="uq_patient_full_name"),
    )
