"""Add extra fields to User

Revision ID: 2e153becf83c
Revises: 
Create Date: 2025-03-10 11:10:09.965397

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '2e153becf83c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('date',
               existing_type=mysql.VARCHAR(length=20),
               type_=sa.String(length=12),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dob', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('place', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('address', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image', sa.String(length=255), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('image')
        batch_op.drop_column('address')
        batch_op.drop_column('place')
        batch_op.drop_column('dob')

    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('date',
               existing_type=sa.String(length=12),
               type_=mysql.VARCHAR(length=20),
               existing_nullable=True,
               existing_server_default=sa.text('current_timestamp()'))

    # ### end Alembic commands ###
