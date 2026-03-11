"""Initial schema."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE sourcetype AS ENUM ('indicator', 'news', 'community');
        CREATE TYPE connectorstatus AS ENUM ('active', 'disabled', 'mock');
        CREATE TYPE jobstatus AS ENUM ('pending', 'running', 'success', 'failed');
        """
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.Enum(name="sourcetype", create_type=False), nullable=False),
        sa.Column("country", sa.String(length=50)),
        sa.Column("base_url", sa.String(length=500)),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("compliance_notes", sa.Text()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sources_code", "sources", ["code"])
    op.create_index("ix_sources_source_type", "sources", ["source_type"])
    op.create_index("ix_sources_country", "sources", ["country"])

    op.create_table(
        "source_connectors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("connector_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.Enum(name="connectorstatus", create_type=False), nullable=False),
        sa.Column("schedule_cron", sa.String(length=100)),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("robots_checked_at", sa.DateTime(timezone=True)),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("source_id", "name", name="uq_source_connector_name"),
    )

    op.create_table(
        "economic_indicators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=50)),
        sa.Column("frequency", sa.String(length=50)),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("description", sa.Text()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("code", "country", name="uq_indicator_code_country"),
    )

    op.create_table(
        "indicator_releases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("indicator_id", sa.Integer(), sa.ForeignKey("economic_indicators.id", ondelete="CASCADE"), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False),
        sa.Column("release_date", sa.Date(), nullable=False),
        sa.Column("release_time", sa.Time()),
        sa.Column("actual_value", sa.Numeric(18, 4)),
        sa.Column("forecast_value", sa.Numeric(18, 4)),
        sa.Column("previous_value", sa.Numeric(18, 4)),
        sa.Column("unit", sa.String(length=50)),
        sa.Column("importance", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("source_url", sa.String(length=500)),
        sa.Column("released_at", sa.DateTime(timezone=True)),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("indicator_id", "country", "release_date", "release_time", name="uq_indicator_release"),
    )

    op.create_table(
        "article_clusters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cluster_key", sa.String(length=128), nullable=False, unique=True),
        sa.Column("topic_label", sa.String(length=255)),
        sa.Column("summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cluster_id", sa.Integer(), sa.ForeignKey("article_clusters.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("author", sa.String(length=255)),
        sa.Column("publisher", sa.String(length=255)),
        sa.Column("canonical_url", sa.String(length=1000), nullable=False),
        sa.Column("original_url", sa.String(length=1000)),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="ko"),
        sa.Column("category", sa.String(length=100)),
        sa.Column("tags_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("title_hash", sa.String(length=64), nullable=False),
        sa.Column("body_hash", sa.String(length=64), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("canonical_url", name="uq_article_canonical_url"),
    )

    op.create_table(
        "community_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("board_name", sa.String(length=255), nullable=False),
        sa.Column("external_post_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author_hash", sa.String(length=128)),
        sa.Column("view_count", sa.Integer()),
        sa.Column("upvotes", sa.Integer()),
        sa.Column("downvotes", sa.Integer()),
        sa.Column("comment_count", sa.Integer()),
        sa.Column("original_url", sa.String(length=1000), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("source_id", "external_post_id", name="uq_community_external_post"),
    )

    op.create_table(
        "community_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_comment_id", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("author_hash", sa.String(length=128)),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("post_id", "external_comment_id", name="uq_community_external_comment"),
    )

    op.create_table(
        "entities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("aliases_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.UniqueConstraint("name", "entity_type", name="uq_entity_name_type"),
    )

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100)),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.UniqueConstraint("code", name="uq_topic_code"),
    )

    op.create_table(
        "sentiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fear_greed_score", sa.Float(), nullable=False, server_default="50"),
        sa.Column("hate_index", sa.Float(), nullable=False, server_default="0"),
        sa.Column("uncertainty_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_bias", sa.String(length=20), nullable=False),
        sa.Column("keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("entities_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("topics_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("document_type", "document_id", name="uq_sentiment_document"),
    )

    op.create_table(
        "document_tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("tag_type", sa.String(length=50), nullable=False),
        sa.Column("tag_value", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("document_type", "document_id", "tag_type", "tag_value", name="uq_document_tag"),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("schedule_cron", sa.String(length=100)),
        sa.Column("status", sa.Enum(name="jobstatus", create_type=False), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True)),
        sa.Column("next_run_at", sa.DateTime(timezone=True)),
        sa.Column("last_success_at", sa.DateTime(timezone=True)),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.UniqueConstraint("name", name="uq_ingestion_job_name"),
    )

    op.create_table(
        "ingestion_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), sa.ForeignKey("ingestion_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum(name="jobstatus", create_type=False), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.create_table(
        "daily_market_sentiment_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("country", sa.String(length=50), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("fear_greed_score", sa.Float(), nullable=False),
        sa.Column("hate_index", sa.Float(), nullable=False),
        sa.Column("uncertainty_score", sa.Float(), nullable=False),
        sa.Column("bullish_ratio", sa.Float(), nullable=False),
        sa.Column("bearish_ratio", sa.Float(), nullable=False),
        sa.Column("neutral_ratio", sa.Float(), nullable=False),
        sa.Column("top_keywords_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("source_counts_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("snapshot_date", "country", name="uq_snapshot_date_country"),
    )


def downgrade() -> None:
    for table in [
        "daily_market_sentiment_snapshots",
        "ingestion_logs",
        "ingestion_jobs",
        "document_tags",
        "sentiments",
        "topics",
        "entities",
        "community_comments",
        "community_posts",
        "articles",
        "article_clusters",
        "indicator_releases",
        "economic_indicators",
        "source_connectors",
        "sources",
    ]:
        op.drop_table(table)

    op.execute(
        """
        DROP TYPE IF EXISTS jobstatus;
        DROP TYPE IF EXISTS connectorstatus;
        DROP TYPE IF EXISTS sourcetype;
        """
    )
