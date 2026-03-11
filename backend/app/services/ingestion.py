from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.rule_based import RuleBasedAnalyzer
from app.analytics.snapshots import calculate_daily_snapshot
from app.collectors.communities.dcinside import DCInsideConnector
from app.collectors.indicators.fred import FredIndicatorCollector
from app.collectors.indicators.fx import FrankfurterFxCollector
from app.collectors.news.rss import RssNewsCollector
from app.models import Article, CommunityPost, IngestionJob, IngestionLog, JobStatus, Sentiment
from app.services.community_analysis import CommunityAnalysisService


class IngestionService:
    def __init__(self) -> None:
        self.analyzer = RuleBasedAnalyzer()
        self.community_analysis = CommunityAnalysisService()
        self.dcinside_connector = DCInsideConnector()
        self.collector_map = {
            "collect_indicators": [FredIndicatorCollector(), FrankfurterFxCollector()],
            "collect_news": [RssNewsCollector()],
            "collect_community": [],
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
                snapshot = calculate_daily_snapshot(db, datetime.now(tz=timezone.utc).date())
                total = 1
                messages.append(f"Snapshot saved for {snapshot.snapshot_date}.")
            elif job_name == "collect_community":
                result = self.dcinside_connector.collect_live(
                    db,
                    board_ids=["stockus"],
                    max_pages=1,
                    max_posts=30,
                )
                total += result.records_processed
                if result.message:
                    messages.append(result.message)
                analyzed = self.community_analysis.backfill_recent_posts(db, limit=30, board_name="stockus-concept")
                messages.append(f"Reanalyzed {analyzed} recent stockus concept posts.")
            else:
                for collector in self.collector_map.get(job_name, []):
                    result = collector.collect(db)
                    total += result.records_processed
                    if result.message:
                        messages.append(result.message)
                self._refresh_sentiments(db)

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

    def _refresh_sentiments(self, db: Session) -> None:
        articles = db.execute(select(Article)).scalars().all()
        posts = db.execute(select(CommunityPost)).scalars().all()
        for row in articles:
            exists = db.execute(
                select(Sentiment).where(
                    Sentiment.document_type == "article",
                    Sentiment.document_id == row.id,
                )
            ).scalar_one_or_none()
            if exists:
                continue
            analysis = self.analyzer.analyze(row.title, row.body)
            db.add(
                Sentiment(
                    document_type="article",
                    document_id=row.id,
                    sentiment_score=analysis.sentiment_score,
                    fear_greed_score=analysis.fear_greed_score,
                    hate_index=analysis.hate_index,
                    uncertainty_score=analysis.uncertainty_score,
                    market_bias=analysis.market_bias,
                    keywords_json=analysis.keywords,
                    entities_json=analysis.entities,
                    topics_json=analysis.topics,
                )
            )

        for row in posts:
            self.community_analysis.persist_post_analysis(db, row)

        db.commit()

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
