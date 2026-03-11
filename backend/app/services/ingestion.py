from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.analytics.rule_based import RuleBasedAnalyzer
from app.analytics.snapshots import calculate_daily_snapshot
from app.collectors.communities.arca_live import ArcaLiveConnector
from app.collectors.communities.live_forums import BobaedreamConnector, ClienConnector, PpomppuConnector
from app.collectors.indicators.fred import FredIndicatorCollector
from app.collectors.indicators.fx import FrankfurterFxCollector
from app.collectors.news.rss import RssNewsCollector
from app.core.config import get_settings
from app.models import Article, CommunityPost, IngestionJob, IngestionLog, JobStatus, Sentiment


class IngestionService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.analyzer = RuleBasedAnalyzer()
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
                if job_name in {"collect_news", "collect_community", "collect_arca_stock"}:
                    snapshot_count = self._refresh_snapshot_range(
                        db,
                        start_date=datetime.now(tz=timezone.utc).date() - timedelta(days=2),
                        end_date=datetime.now(tz=timezone.utc).date(),
                    )
                    messages.append(
                        f"Generated {sentiment_count} sentiment rows and refreshed {snapshot_count} recent snapshots."
                    )
                elif sentiment_count:
                    messages.append(f"Generated {sentiment_count} sentiment rows.")

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
