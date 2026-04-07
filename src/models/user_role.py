import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ASSISTANT_ADMIN = "assistant_admin"
    EMPLOYEE = "employee"
    PATIENT = "patient"
    GUEST = "guest"
