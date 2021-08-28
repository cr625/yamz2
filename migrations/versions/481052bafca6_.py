"""empty message

Revision ID: 481052bafca6
Revises: 8f708ea0e64a
Create Date: 2021-08-27 23:35:46.328101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '481052bafca6'
down_revision = '8f708ea0e64a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('votes', sa.Column('vote_type', sa.Text(), nullable=True))
    op.drop_column('votes', 'vote')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('votes', sa.Column('vote', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('votes', 'vote_type')
    # ### end Alembic commands ###
