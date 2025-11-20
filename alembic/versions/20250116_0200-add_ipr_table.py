"""Add infrastructure_pull_requests table

Revision ID: 002
Revises: 001
Create Date: 2025-01-16 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "infrastructure_pull_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("blueprint_id", sa.Integer(), nullable=False),
        sa.Column("blueprint_snapshot", sa.JSON(), nullable=False),
        sa.Column("changes_summary", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "APPROVED",
                "REJECTED",
                "DEPLOYED",
                "FAILED",
                "CANCELLED",
                name="iprstatus",
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("reviewed_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("deployed_at", sa.DateTime(), nullable=True),
        sa.Column("deployment_id", sa.String(length=255), nullable=True),
        sa.Column("review_comments", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_infrastructure_pull_requests_id"),
        "infrastructure_pull_requests",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_infrastructure_pull_requests_blueprint_id"),
        "infrastructure_pull_requests",
        ["blueprint_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_infrastructure_pull_requests_status"),
        "infrastructure_pull_requests",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_index(
        op.f("ix_infrastructure_pull_requests_status"), table_name="infrastructure_pull_requests"
    )
    op.drop_index(
        op.f("ix_infrastructure_pull_requests_blueprint_id"),
        table_name="infrastructure_pull_requests",
    )
    op.drop_index(
        op.f("ix_infrastructure_pull_requests_id"), table_name="infrastructure_pull_requests"
    )
    op.drop_table("infrastructure_pull_requests")
