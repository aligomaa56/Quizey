"""DEL: Del avatar col

Revision ID: d4f5a419bd73
Revises: 7372a68e2dc5
Create Date: 2024-09-03 04:32:41.934142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f5a419bd73'
down_revision: Union[str, None] = '7372a68e2dc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'avatar')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('avatar', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
