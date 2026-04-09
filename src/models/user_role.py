import enum


class UserRole(str, enum.Enum):
    GUEST = "guest"
    ADMIN = "admin"
    ASSISTANT_ADMIN = "assistant_admin"
    EMPLOYEE = "employee"
    PATIENT = "patient"
