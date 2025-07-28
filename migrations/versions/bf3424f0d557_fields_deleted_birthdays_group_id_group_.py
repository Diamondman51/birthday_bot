"""fields deleted Birthdays: group_id, group. Groups: birthdays

Revision ID: bf3424f0d557
Revises: 4e81f38891ab
Create Date: 2025-07-28 22:48:10.939478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf3424f0d557'
down_revision: Union[str, None] = '4e81f38891ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    with op.batch_alter_table('birthdays', schema=None) as batch_op:
        batch_op.drop_column('group_id')


def downgrade() -> None:
    with op.batch_alter_table('birthdays', schema=None) as batch_op:
        batch_op.add_column(sa.Column('group_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'groups', ['group_id'], ['id'])