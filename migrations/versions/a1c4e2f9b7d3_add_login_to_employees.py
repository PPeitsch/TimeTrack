"""Add login columns to employees

Revision ID: a1c4e2f9b7d3
Revises: 30dae3457b0c
Create Date: 2026-10-03 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1c4e2f9b7d3"
down_revision = "30dae3457b0c"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("employees") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("password_hash", sa.String(), nullable=True))
        batch_op.create_unique_constraint("uq_employees_username", ["username"])


def downgrade():
    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_constraint("uq_employees_username", type_="unique")
        batch_op.drop_column("password_hash")
        batch_op.drop_column("username")
