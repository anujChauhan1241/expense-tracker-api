"""Add user_id to expenses

Revision ID: 99bcbd25b8a6
Revises: 477efa804ad2
Create Date: 2026-10-08 01:07:12.935726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99bcbd25b8a6'
down_revision = '477efa804ad2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('user_id', sa.Integer(), nullable=True)
        )

        batch_op.create_foreign_key(
            'fk_expense_user_id',
            'user',
            ['user_id'],
            ['id']
        )


def downgrade():
    with op.batch_alter_table('expense', schema=None) as batch_op:
        batch_op.drop_constraint(
            'fk_expense_user_id',
            type_='foreignkey'
        )

        batch_op.drop_column('user_id')
