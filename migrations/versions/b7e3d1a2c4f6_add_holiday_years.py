"""Add holiday_years to track loaded holiday years

Revision ID: b7e3d1a2c4f6
Revises: a1c4e2f9b7d3
Create Date: 2026-10-03 14:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7e3d1a2c4f6"
down_revision = "a1c4e2f9b7d3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "holiday_years",
        sa.Column("year", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("year"),
    )


def downgrade():
    op.drop_table("holiday_years")
