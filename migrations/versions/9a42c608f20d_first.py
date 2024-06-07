"""First

Revision ID: 9a42c608f20d
Revises: ebd41bc6cf4a
Create Date: 2024-06-07 21:11:44.198580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a42c608f20d'
down_revision: Union[str, None] = 'ebd41bc6cf4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contacts', sa.Column('first_name', sa.String(length=25), nullable=False))
    op.add_column('contacts', sa.Column('last_name', sa.String(length=50), nullable=False))
    op.drop_column('contacts', 'fullname')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contacts', sa.Column('fullname', sa.VARCHAR(length=50), autoincrement=False, nullable=False))
    op.drop_column('contacts', 'last_name')
    op.drop_column('contacts', 'first_name')
    # ### end Alembic commands ###