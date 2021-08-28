"""empty message

Revision ID: dbc20a5d3938
Revises: 481052bafca6
Create Date: 2021-08-28 14:57:45.309512

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dbc20a5d3938'
down_revision = '481052bafca6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('body_html', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('disabled', sa.Boolean(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('term_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['term_id'], ['terms.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comments_timestamp'), 'comments', ['timestamp'], unique=False)
    op.create_table('follows',
    sa.Column('follower_id', sa.Integer(), nullable=False),
    sa.Column('followed_id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['terms.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['terms.id'], ),
    sa.PrimaryKeyConstraint('follower_id', 'followed_id')
    )
    op.create_table('relationships',
    sa.Column('parent_id', sa.Integer(), nullable=False),
    sa.Column('child_id', sa.Integer(), nullable=False),
    sa.Column('predicate', sa.String(length=64), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['child_id'], ['terms.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['terms.id'], ),
    sa.PrimaryKeyConstraint('parent_id', 'child_id')
    )
    op.create_table('votes',
    sa.Column('voter_id', sa.Integer(), nullable=False),
    sa.Column('term_id', sa.Integer(), nullable=False),
    sa.Column('vote_type', sa.Text(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['term_id'], ['terms.id'], ),
    sa.ForeignKeyConstraint(['voter_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('voter_id', 'term_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('votes')
    op.drop_table('relationships')
    op.drop_table('follows')
    op.drop_index(op.f('ix_comments_timestamp'), table_name='comments')
    op.drop_table('comments')
    # ### end Alembic commands ###
