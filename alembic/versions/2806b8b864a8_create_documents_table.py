"""create documents table

Revision ID: 2806b8b864a8
Revises: 65bed47a1cb2
Create Date: 2026-07-16 16:50:38.199606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2806b8b864a8'
down_revision: Union[str, Sequence[str], None] = '65bed47a1cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('documents',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('s3_key', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('s3_key')
    )
    op.create_index(op.f('ix_documents_owner_id'), 'documents', ['owner_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_documents_owner_id'), table_name='documents')
    op.drop_table('documents')