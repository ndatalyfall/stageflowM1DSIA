"""create StageFlow tables

Revision ID: 0001_create_stageflow_tables
Revises:
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_stageflow_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial StageFlow schema."""
    role_values = ["student", "company", "program_manager", "admin"]
    offer_status_values = ["draft", "submitted", "published", "rejected"]
    application_status_values = ["pending", "accepted", "rejected", "withdrawn"]

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum(*role_values, name="role_name", native_enum=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("mission", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("status", sa.Enum(*offer_status_values, name="offer_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["users.id"]),
    )
    op.create_index("ix_offers_company_id", "offers", ["company_id"], unique=False)
    op.create_index("ix_offers_status", "offers", ["status"], unique=False)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("cover_letter", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum(*application_status_values, name="application_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["offer_id"], ["offers.id"]),
    )
    op.create_index("ix_applications_student_id", "applications", ["student_id"], unique=False)
    op.create_index("ix_applications_offer_id", "applications", ["offer_id"], unique=False)
    op.create_index("ix_applications_status", "applications", ["status"], unique=False)


def downgrade() -> None:
    """Drop the initial StageFlow schema."""
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_offer_id", table_name="applications")
    op.drop_index("ix_applications_student_id", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_offers_status", table_name="offers")
    op.drop_index("ix_offers_company_id", table_name="offers")
    op.drop_table("offers")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
