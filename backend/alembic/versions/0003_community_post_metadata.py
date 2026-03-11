"""Add community post metadata for source boards and topic category."""

from alembic import op
import sqlalchemy as sa


revision = "0003_community_post_metadata"
down_revision = "0002_politics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("community_posts", sa.Column("board_code", sa.String(length=100), nullable=True))
    op.add_column("community_posts", sa.Column("topic_category", sa.String(length=50), nullable=True))
    op.create_index("ix_community_posts_board_code", "community_posts", ["board_code"])
    op.create_index("ix_community_posts_topic_category", "community_posts", ["topic_category"])
    op.create_index(
        "ix_community_posts_topic_lookup",
        "community_posts",
        ["topic_category", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_posts_topic_lookup", table_name="community_posts")
    op.drop_index("ix_community_posts_topic_category", table_name="community_posts")
    op.drop_index("ix_community_posts_board_code", table_name="community_posts")
    op.drop_column("community_posts", "topic_category")
    op.drop_column("community_posts", "board_code")
