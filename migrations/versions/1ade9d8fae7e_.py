"""empty message

Revision ID: 1ade9d8fae7e
Revises: c3e6aad93f37
Create Date: 2021-09-05 21:03:12.400795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ade9d8fae7e'
down_revision = 'c3e6aad93f37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('term_id', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=64), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['term_id'], ['terms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sets')
    # ### end Alembic commands ###