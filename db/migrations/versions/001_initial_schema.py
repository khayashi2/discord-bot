"""Initial schema: guilds, channels, members, messages.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-04-03

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guilds",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("icon_url", sa.String(512), nullable=True),
        sa.Column("member_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "channels",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "members",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(512), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["guild_id"], ["guilds.id"]),
        sa.PrimaryKeyConstraint("id", "guild_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("channel_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("author_guild_id", sa.BigInteger(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("content_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "has_attachments", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("has_embeds", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("emoji_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["channel_id"], ["channels.id"]),
        sa.ForeignKeyConstraint(
            ["author_id", "author_guild_id"], ["members.id", "members.guild_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("members")
    op.drop_table("channels")
    op.drop_table("guilds")
