"""create_initial_users

Revision ID: f219336167a2
Revises:
Create Date: 2026-04-08 00:25:07.460336

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from src.models.user_role import UserRole

# revision identifiers, used by Alembic.
revision: str = "f219336167a2"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # User Table Creation
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("uid", sa.String(length=36), nullable=False, unique=True, index=True),
        sa.Column("firstName", sa.String(length=100), nullable=False),
        sa.Column("lastName", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False, unique=True),
        sa.Column("password", sa.String(length=200), nullable=True),
        sa.Column(
            "role",
            sa.Enum(*[r.value for r in UserRole], name="userrole"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
    )

    """Upgrade schema."""
    user_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("uid", sa.String),
        sa.column("firstName", sa.String),
        sa.column("lastName", sa.String),
        sa.column("email", sa.String),
        sa.column("password", sa.String),
        sa.column("role", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        user_table,
        [
            {
                "uid": "999e4567-e89b-12d3-a456-426614174000",
                "firstName": "Guest",
                "lastName": "User",
                "email": "guest@email.com",
                "password": None,
                "role": UserRole.GUEST.value,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
            {
                "uid": "c1ca2bc2-b63a-4deb-8829-9985763637b6",
                "firstName": "Admin",
                "lastName": "User",
                "email": "admin@email.com",
                "password": None,
                "role": UserRole.ADMIN.value,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM users WHERE email IN ('guest@email.com')")
    op.drop_table("users")
