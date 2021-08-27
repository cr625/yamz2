"""empty message

Revision ID: 5eecdbeeb08f
Revises: 19c321cad17e
Create Date: 2021-08-25 17:34:59.773469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5eecdbeeb08f'
down_revision = '19c321cad17e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('follows_follower_id_fkey', 'follows', type_='foreignkey')
    op.drop_constraint('follows_followed_id_fkey', 'follows', type_='foreignkey')
    op.create_foreign_key(None, 'follows', 'terms', ['followed_id'], ['id'])
    op.create_foreign_key(None, 'follows', 'terms', ['follower_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'follows', type_='foreignkey')
    op.drop_constraint(None, 'follows', type_='foreignkey')
    op.create_foreign_key('follows_followed_id_fkey', 'follows', 'users', ['followed_id'], ['id'])
    op.create_foreign_key('follows_follower_id_fkey', 'follows', 'users', ['follower_id'], ['id'])
    # ### end Alembic commands ###