"""update report system

Revision ID: 5cafa02cee0b
Revises: 8b0b7766ecc4
Create Date: 2025-05-18 10:58:09.338138

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5cafa02cee0b"
down_revision: Union[str, None] = "8b0b7766ecc4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "report_msg",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("msg_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("report_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_table("report_bottle")
    op.add_column(
        "bot_user", sa.Column("warns", sa.Integer(), server_default="0", nullable=False)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("bot_user", "warns")
    op.create_table(
        "report_bottle",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("bottle", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("report_author", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bottle"],
            ["bottle.id"],
            name="report_bottle_bottle_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["report_author"],
            ["bot_user.tg_id"],
            name="report_bottle_report_author_fkey",
        ),
        sa.PrimaryKeyConstraint("id", name="report_bottle_pkey"),
    )
    op.drop_table("report_msg")
    # ### end Alembic commands ###
