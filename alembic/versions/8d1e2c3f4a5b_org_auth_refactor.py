"""org_auth_refactor

Revision ID: 8d1e2c3f4a5b
Revises: f1000e8f3cd9
Create Date: 2026-01-15 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d1e2c3f4a5b"
down_revision: Union[str, None] = "f1000e8f3cd9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add organization auth fields
    op.add_column("organizations", sa.Column("email", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("password", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("phone_number", sa.String(), nullable=True))
    op.add_column("organizations", sa.Column("address", sa.String(), nullable=True))
    op.create_index(op.f("ix_organizations_email"), "organizations", ["email"], unique=True)

    # Drop audit_logs.actor_user_id FK + column if present
    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.drop_column("actor_user_id")

    # Drop users table if it exists
    op.execute("DROP TABLE IF EXISTS users CASCADE")


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate users table (minimal columns)
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
    )

    with op.batch_alter_table("loans") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key("loans_user_id_fkey", "users", ["user_id"], ["id"], ondelete="SET NULL")

    with op.batch_alter_table("audit_logs") as batch_op:
        batch_op.add_column(sa.Column("actor_user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key("audit_logs_actor_user_id_fkey", "users", ["actor_user_id"], ["id"], ondelete="SET NULL")

    op.drop_index(op.f("ix_organizations_email"), table_name="organizations")
    op.drop_column("organizations", "address")
    op.drop_column("organizations", "phone_number")
    op.drop_column("organizations", "password")
    op.drop_column("organizations", "email")
