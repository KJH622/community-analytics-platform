"""politics domain schema"""

from alembic import op
import sqlalchemy as sa


revision = "0002_politics"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "political_parties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="KR"),
        sa.Column("ideology", sa.String(length=100)),
        sa.Column("description", sa.Text()),
        sa.Column("official_color", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("name", "country", name="uq_political_party_name_country"),
    )
    op.create_table(
        "politicians",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("party", sa.String(length=255)),
        sa.Column("party_id", sa.Integer(), sa.ForeignKey("political_parties.id", ondelete="SET NULL")),
        sa.Column("position", sa.String(length=255)),
        sa.Column("ideology", sa.String(length=100)),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="KR"),
        sa.Column("start_term", sa.Date()),
        sa.Column("end_term", sa.Date()),
        sa.Column("aliases_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("name", "country", name="uq_politician_name_country"),
    )
    op.create_table(
        "political_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("indicator_name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="KR"),
        sa.Column("description", sa.Text()),
        sa.Column("unit", sa.String(length=50)),
        sa.Column("source", sa.String(length=255)),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("code", "country", name="uq_political_indicator_code_country"),
    )
    op.create_table(
        "political_indicator_values",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("political_indicators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("label", sa.String(length=255)),
        sa.Column("source", sa.String(length=255)),
        sa.Column("unit", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("indicator_id", "date", "label", name="uq_political_indicator_value"),
    )
    op.create_table(
        "political_topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100)),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.UniqueConstraint("code", name="uq_political_topic_code"),
    )
    op.create_table(
        "political_entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("name", "entity_type", name="uq_political_entity_name_type"),
    )
    op.create_table(
        "political_community_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("leaning", sa.String(length=100)),
        sa.Column("link", sa.String(length=500), nullable=False),
        sa.Column("board_name", sa.String(length=255)),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="disabled"),
        sa.Column("compliance_notes", sa.Text()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("code", name="uq_political_community_source_code"),
    )
    op.create_table(
        "political_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_code", sa.String(length=100), nullable=False),
        sa.Column("community_name", sa.String(length=255), nullable=False),
        sa.Column("board_name", sa.String(length=255)),
        sa.Column("external_post_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("view_count", sa.Integer()),
        sa.Column("upvotes", sa.Integer()),
        sa.Column("comment_count", sa.Integer()),
        sa.Column("original_url", sa.String(length=1000), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("source_code", "external_post_id", name="uq_political_post_source_external"),
    )
    op.create_table(
        "political_sentiment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("political_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("political_sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("support_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("opposition_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("anger_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("mockery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("political_hate_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("apathy_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("enthusiasm_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("political_polarization_index", sa.Float(), nullable=False, server_default="0"),
        sa.Column("election_heat_index", sa.Float(), nullable=False, server_default="0"),
        sa.Column("politician_mentions_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("labels_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("post_id", name="uq_political_sentiment_post"),
    )
    op.create_table(
        "political_daily_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False, server_default="KR"),
        sa.Column("political_sentiment_score", sa.Float(), nullable=False),
        sa.Column("political_polarization_index", sa.Float(), nullable=False),
        sa.Column("election_heat_index", sa.Float(), nullable=False),
        sa.Column("top_keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("top_politicians_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("source_counts_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("snapshot_date", "country", name="uq_political_snapshot_date_country"),
    )


def downgrade() -> None:
    for table in [
        "political_daily_snapshot",
        "political_sentiment",
        "political_posts",
        "political_community_sources",
        "political_entities",
        "political_topics",
        "political_indicator_values",
        "political_indicators",
        "politicians",
        "political_parties",
    ]:
        op.drop_table(table)
