from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.analytics.openai_community import OpenAICommunityAnalyzer
from app.analytics.rule_based import RuleBasedAnalyzer
from app.analytics.snapshots import calculate_daily_snapshot
from app.collectors.communities.arca_live import ArcaLiveConnector
from app.collectors.communities.live_forums import BobaedreamConnector, ClienConnector, PpomppuConnector
from app.collectors.indicators.fred import FredIndicatorCollector
from app.collectors.indicators.fx import FrankfurterFxCollector
from app.collectors.news.rss import RssNewsCollector
from app.core.config import get_settings
from app.models import (
    Article,
    CommunityPost,
    DocumentTag,
    IngestionJob,
    IngestionLog,
    JobStatus,
    Sentiment,
    Source,
)


class IngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.analyzer = RuleBasedAnalyzer()
        self.openai_analyzer = OpenAICommunityAnalyzer(self.settings)
        self.community_collectors = [PpomppuConnector(), BobaedreamConnector(), ClienConnector()]
        self.arca_collectors = [ArcaLiveConnector()]
        self.collector_map = {
            "collect_indicators": [FredIndicatorCollector(), FrankfurterFxCollector()],
            "collect_news": [RssNewsCollector()],
            "collect_community": self.community_collectors,
            "collect_arca_stock": self.arca_collectors,
            "backfill_community_history": self.community_collectors,
            "refresh_snapshots": [],
        }

    def run_job(self, db: Session, job_name: str) -> tuple[JobStatus, str, int]:
        job = db.execute(select(IngestionJob).where(IngestionJob.name == job_name)).scalar_one_or_none()
        if job is None:
            job = IngestionJob(
                name=job_name,
                description=f"On-demand job runner for {job_name}",
                source_type=job_name.replace("collect_", ""),
                status=JobStatus.PENDING,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        job.status = JobStatus.RUNNING
        job.last_run_at = datetime.now(tz=timezone.utc)
        db.commit()

        total = 0
        messages: list[str] = []
        try:
            if job_name == "refresh_snapshots":
                rebuilt = self._refresh_snapshot_range(
                    db,
                    start_date=datetime.now(tz=timezone.utc).date()
                    - timedelta(days=self.settings.community_history_days),
                    end_date=datetime.now(tz=timezone.utc).date(),
                )
                total = rebuilt
                messages.append(f"Rebuilt {rebuilt} daily snapshots.")
            elif job_name == "backfill_community_history":
                for collector in self.community_collectors:
                    result = collector.collect_history(db, days=self.settings.community_history_days)
                    total += result.records_processed
                    if result.message:
                        messages.append(result.message)
                sentiment_count = self._refresh_sentiments(db)
                snapshot_count = self._refresh_snapshot_range(
                    db,
                    start_date=datetime.now(tz=timezone.utc).date()
                    - timedelta(days=self.settings.community_history_days),
                    end_date=datetime.now(tz=timezone.utc).date(),
                )
                messages.append(
                    f"Generated {sentiment_count} sentiment rows and rebuilt {snapshot_count} daily snapshots."
                )
            else:
                for collector in self.collector_map.get(job_name, []):
                    result = collector.collect(db)
                    total += result.records_processed
                    if result.message:
                        messages.append(result.message)
                sentiment_count = self._refresh_sentiments(db)
                openai_count = self._refresh_openai_community_sentiments(db)
                if job_name in {"collect_news", "collect_community", "collect_arca_stock"}:
                    snapshot_count = self._refresh_snapshot_range(
                        db,
                        start_date=datetime.now(tz=timezone.utc).date() - timedelta(days=2),
                        end_date=datetime.now(tz=timezone.utc).date(),
                    )
                    if openai_count:
                        messages.append(f"Updated {openai_count} OpenAI community sentiment rows.")
                    messages.append(
                        f"Generated {sentiment_count} sentiment rows and refreshed {snapshot_count} recent snapshots."
                    )
                elif sentiment_count:
                    messages.append(f"Generated {sentiment_count} sentiment rows.")
                elif openai_count:
                    messages.append(f"Updated {openai_count} OpenAI community sentiment rows.")

            job.status = JobStatus.SUCCESS
            job.last_success_at = datetime.now(tz=timezone.utc)
            message = " ".join(messages) if messages else "Job completed."
            self._log(db, job, JobStatus.SUCCESS, message, total)
            db.commit()
            return JobStatus.SUCCESS, message, total
        except Exception as exc:
            db.rollback()
            job.status = JobStatus.FAILED
            message = f"Job failed: {exc}"
            self._log(db, job, JobStatus.FAILED, message, total)
            db.commit()
            return JobStatus.FAILED, message, total

    def _refresh_sentiments(self, db: Session) -> int:
        created = 0
        document_specs = [
            ("article", Article, "published_at"),
            ("community_post", CommunityPost, "created_at"),
        ]

        for document_type, model, timestamp_attr in document_specs:
            rows = db.execute(
                select(model)
                .outerjoin(
                    Sentiment,
                    and_(
                        Sentiment.document_type == document_type,
                        Sentiment.document_id == model.id,
                    ),
                )
                .where(Sentiment.id.is_(None))
            ).scalars().all()

            for row in rows:
                analysis = self.analyzer.analyze(row.title, row.body)
                db.add(
                    Sentiment(
                        document_type=document_type,
                        document_id=row.id,
                        sentiment_score=analysis.sentiment_score,
                        fear_greed_score=analysis.fear_greed_score,
                        hate_index=analysis.hate_index,
                        uncertainty_score=analysis.uncertainty_score,
                        market_bias=analysis.market_bias,
                        keywords_json=analysis.keywords,
                        entities_json=analysis.entities,
                        topics_json=analysis.topics,
                        created_at=getattr(row, timestamp_attr),
                    )
                )
                created += 1

        db.commit()
        return created

    def _refresh_openai_community_sentiments(self, db: Session) -> int:
        if not self.openai_analyzer.enabled:
            return 0

        posts = db.execute(
            select(CommunityPost)
            .join(Source, CommunityPost.source_id == Source.id)
            .where(Source.code == "arca_live")
            .order_by(CommunityPost.created_at.desc())
            .limit(self.settings.openai_community_post_limit)
        ).scalars().all()
        if not posts:
            return 0

        post_ids = [post.id for post in posts]
        sentiments = db.execute(
            select(Sentiment).where(
                Sentiment.document_type == "community_post",
                Sentiment.document_id.in_(post_ids),
            )
        ).scalars().all()
        sentiment_map = {item.document_id: item for item in sentiments}

        provider_tags = db.execute(
            select(DocumentTag).where(
                DocumentTag.document_type == "community_post",
                DocumentTag.document_id.in_(post_ids),
                DocumentTag.tag_type == "analysis_provider",
            )
        ).scalars().all()
        tag_map = {item.document_id: item for item in provider_tags}

        updated = 0
        for post in posts:
            content_hash = sha256(f"{post.title}\n{post.body}".encode("utf-8")).hexdigest()
            provider_tag = tag_map.get(post.id)
            metadata = provider_tag.metadata_json if provider_tag else {}
            if (
                provider_tag is not None
                and provider_tag.tag_value == "openai"
                and metadata.get("content_hash") == content_hash
                and metadata.get("model") == self.openai_analyzer.model
            ):
                continue

            result = self.openai_analyzer.analyze(post.title, post.body)
            analysis = result.analysis
            sentiment = sentiment_map.get(post.id)
            if sentiment is None:
                sentiment = Sentiment(
                    document_type="community_post",
                    document_id=post.id,
                    created_at=post.created_at,
                )
                db.add(sentiment)
                sentiment_map[post.id] = sentiment

            sentiment.sentiment_score = analysis.sentiment_score
            sentiment.fear_greed_score = analysis.fear_greed_score
            sentiment.hate_index = analysis.hate_index
            sentiment.uncertainty_score = analysis.uncertainty_score
            sentiment.market_bias = analysis.market_bias
            sentiment.keywords_json = analysis.keywords
            sentiment.entities_json = analysis.entities
            sentiment.topics_json = analysis.topics
            sentiment.created_at = post.created_at

            if provider_tag is None:
                provider_tag = DocumentTag(
                    document_type="community_post",
                    document_id=post.id,
                    tag_type="analysis_provider",
                    tag_value=result.provider,
                    metadata_json={},
                )
                db.add(provider_tag)
                tag_map[post.id] = provider_tag

            provider_tag.tag_value = result.provider
            provider_tag.metadata_json = {
                "model": result.model,
                "content_hash": content_hash,
                "updated_at": datetime.now(tz=timezone.utc).isoformat(),
            }
            updated += 1

        db.commit()
        return updated

    def _refresh_snapshot_range(self, db: Session, start_date: date, end_date: date) -> int:
        rebuilt = 0
        current = start_date
        while current <= end_date:
            calculate_daily_snapshot(db, current)
            rebuilt += 1
            current += timedelta(days=1)
        return rebuilt

    def _log(
        self,
        db: Session,
        job: IngestionJob,
        status: JobStatus,
        message: str,
        records_processed: int,
    ) -> None:
        db.add(
            IngestionLog(
                job_id=job.id,
                status=status,
                message=message,
                records_processed=records_processed,
                details_json={},
            )
        )
