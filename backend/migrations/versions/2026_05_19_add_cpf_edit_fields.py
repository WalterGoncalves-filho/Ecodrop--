"""add cpf edit permission fields

Revision ID: add_cpf_edit_fields_001
Revises: add_address_fields_001
Create Date: 2026-05-19 13:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'add_cpf_edit_fields_001'
down_revision: Union[str, None] = 'add_address_fields_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('cpf_edit_allowed', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('usuarios', sa.Column('cpf_notified', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('usuarios', sa.Column('cpf_locked', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('usuarios', 'cpf_locked')
    op.drop_column('usuarios', 'cpf_notified')
    op.drop_column('usuarios', 'cpf_edit_allowed')
