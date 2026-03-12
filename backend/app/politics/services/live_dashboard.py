from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from math import log1p

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import CommunityPost, Sentiment, Source

SOURCE_LABELS = {
    "ppomppu": "뽐뿌",
    "bobaedream": "보배드림",
    "clien": "클리앙",
}

ISSUE_RULES = {
    "government_policy": {
        "label": "정부 정책",
        "keywords": ["정부", "대통령실", "국정", "정책", "공약", "행정"],
    },
    "judiciary": {
        "label": "검찰 / 사법",
        "keywords": ["검찰", "공수처", "경찰", "재판", "법원", "특검", "수사", "사법"],
    },
    "party_conflict": {
        "label": "정당 갈등",
        "keywords": ["민주당", "국민의힘", "국힘", "여야", "야당", "여당", "당대표", "원내대표"],
    },
    "medical_policy": {
        "label": "의료 정책",
        "keywords": ["의대", "증원", "전공의", "의사", "의협", "의정"],
    },
    "defense_policy": {
        "label": "안보 / 국방",
        "keywords": ["북한", "미사일", "국방", "안보", "방산", "대북", "훈련"],
    },
    "election": {
        "label": "선거 / 지지율",
        "keywords": ["선거", "지지율", "대선", "총선", "지선", "후보", "여론조사"],
    },
    "assembly": {
        "label": "국회 / 입법",
        "keywords": ["국회", "법안", "청문회", "의원", "본회의", "상임위", "입법"],
    },
    "general": {
        "label": "정치 일반",
        "keywords": [],
    },
}

POLITICIAN_ALIASES = {
    "이재명": ["이재명"],
    "윤석열": ["윤석열", "윤대통령"],
    "한동훈": ["한동훈"],
    "이준석": ["이준석"],
    "조국": ["조국"],
    "김건희": ["김건희"],
    "홍준표": ["홍준표"],
    "정청래": ["정청래"],
    "안철수": ["안철수"],
    "오세훈": ["오세훈"],
    "박주민": ["박주민"],
}

POSITIVE_TERMS = [
    "지지",
    "찬성",
    "환영",
    "응원",
    "잘한다",
    "잘했",
    "필요",
    "성과",
    "훌륭",
    "좋다",
    "박수",
]

NEGATIVE_TERMS = [
    "반대",
    "비판",
    "문제",
    "논란",
    "실패",
    "최악",
    "부패",
    "의혹",
    "거짓",
    "우려",
    "비난",
    "탄핵",
    "막장",
]

ANGER_TERMS = [
    "분노",
    "열받",
    "혐오",
    "극혐",
    "짜증",
    "미쳤",
    "분개",
    "분탕",
    "패악",
]


@dataclass
class PoliticalDocument:
    post: CommunityPost
    source: Source
    sentiment: Sentiment | None
    source_label: str
    issue_ids: list[str]
    issue_labels: list[str]
    stance: str
    emotion: str
    score: float
    influence_score: float
    mentioned_politicians: set[str]


def build_politics_dashboard(db: Session) -> dict:
    rows = db.execute(
        select(CommunityPost, Source, Sentiment)
        .join(Source, CommunityPost.source_id == Source.id)
        .outerjoin(
            Sentiment,
            and_(Sentiment.document_type == "community_post", Sentiment.document_id == CommunityPost.id),
        )
        .where(CommunityPost.topic_category == "politics")
        .order_by(CommunityPost.created_at.desc())
    ).all()

    documents = [_build_document(post, source, sentiment) for post, source, sentiment in rows]
    if not documents:
        return _empty_dashboard()

    reference_date = max(item.post.created_at.date() for item in documents)
    recent_start = reference_date - timedelta(days=29)
    recent_documents = [item for item in documents if item.post.created_at.date() >= recent_start]
    daily_documents = [item for item in recent_documents if item.post.created_at.date() == reference_date]
    if not daily_documents:
        daily_documents = recent_documents[:]

    issue_stats = _build_issue_stats(recent_documents)
    top_issue = next((item["issue"] for item in issue_stats if item["issue"] != ISSUE_RULES["general"]["label"]), issue_stats[0]["issue"])
    politician_rankings = _build_politician_rankings(daily_documents, recent_documents)

    return {
        "reference_date": reference_date,
        "summary": {
            "reference_date": reference_date,
            "post_count": len(recent_documents),
            "today_post_count": len(daily_documents),
            "community_count": len({item.source.code for item in recent_documents}),
            "top_issue": top_issue,
            "top_politician": politician_rankings[0]["name"] if politician_rankings else None,
        },
        "polarization_trend": _build_polarization_trend(recent_documents, days=14),
        "today_emotion": _build_today_emotion(reference_date, daily_documents),
        "issue_sentiments": issue_stats,
        "issue_source_comparisons": _build_issue_source_comparisons(recent_documents, issue_stats),
        "politician_rankings": politician_rankings,
        "issue_timeline": _build_issue_timeline(recent_documents, days=7),
        "hot_posts": _build_hot_posts(recent_documents),
    }


def _empty_dashboard() -> dict:
    return {
        "reference_date": None,
        "summary": {
            "reference_date": None,
            "post_count": 0,
            "today_post_count": 0,
            "community_count": 0,
            "top_issue": None,
            "top_politician": None,
        },
        "polarization_trend": [],
        "today_emotion": {
            "date": None,
            "anger_pct": 0.0,
            "positive_pct": 0.0,
            "neutral_pct": 0.0,
            "mentions": 0,
        },
        "issue_sentiments": [],
        "issue_source_comparisons": [],
        "politician_rankings": [],
        "issue_timeline": [],
        "hot_posts": [],
    }


def _build_document(post: CommunityPost, source: Source, sentiment: Sentiment | None) -> PoliticalDocument:
    text = _normalized_text(post)
    issue_ids = _detect_issue_ids(text)
    stance, emotion, score = _classify_document(text, sentiment)
    return PoliticalDocument(
        post=post,
        source=source,
        sentiment=sentiment,
        source_label=SOURCE_LABELS.get(source.code, source.name),
        issue_ids=issue_ids,
        issue_labels=[ISSUE_RULES[issue_id]["label"] for issue_id in issue_ids],
        stance=stance,
        emotion=emotion,
        score=score,
        influence_score=_calculate_influence(post, score, sentiment),
        mentioned_politicians=_detect_politicians(text),
    )


def _normalized_text(post: CommunityPost) -> str:
    return f"{post.title} {post.body}".strip()


def _count_terms(text: str, terms: list[str]) -> int:
    return sum(text.count(term) for term in terms)


def _detect_issue_ids(text: str) -> list[str]:
    hits: list[tuple[str, int]] = []
    for issue_id, rule in ISSUE_RULES.items():
        if issue_id == "general":
            continue
        score = _count_terms(text, rule["keywords"])
        if score > 0:
            hits.append((issue_id, score))
    if not hits:
        return ["general"]
    hits.sort(key=lambda item: item[1], reverse=True)
    return [issue_id for issue_id, _ in hits[:2]]


def _detect_politicians(text: str) -> set[str]:
    mentioned: set[str] = set()
    for name, aliases in POLITICIAN_ALIASES.items():
        if any(alias in text for alias in aliases):
            mentioned.add(name)
    return mentioned


def _classify_document(text: str, sentiment: Sentiment | None) -> tuple[str, str, float]:
    positive_hits = _count_terms(text, POSITIVE_TERMS)
    negative_hits = _count_terms(text, NEGATIVE_TERMS)
    anger_hits = _count_terms(text, ANGER_TERMS)
    sentiment_score = sentiment.sentiment_score if sentiment else 0.0
    hate_index = sentiment.hate_index if sentiment else 0.0
    score = sentiment_score + (positive_hits * 7) - (negative_hits * 7) - (anger_hits * 5) - (hate_index * 0.35)

    if score >= 7:
        stance = "support"
    elif score <= -7 or hate_index >= 12 or anger_hits >= 2:
        stance = "oppose"
    else:
        stance = "neutral"

    if anger_hits > 0 or hate_index >= 8 or negative_hits >= 2:
        emotion = "anger"
    elif stance == "support":
        emotion = "positive"
    else:
        emotion = "neutral"

    return stance, emotion, round(score, 2)


def _calculate_influence(post: CommunityPost, score: float, sentiment: Sentiment | None) -> float:
    view_count = post.view_count or 0
    comment_count = post.comment_count or 0
    upvotes = post.upvotes or 0
    hate_index = sentiment.hate_index if sentiment else 0.0
    return round((log1p(max(view_count, 0)) * 12) + (comment_count * 2.5) + (upvotes * 1.8) + abs(score) + (hate_index * 0.4), 2)


def _build_issue_stats(documents: list[PoliticalDocument]) -> list[dict]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    mentions: Counter[str] = Counter()

    for item in documents:
        for issue_id in item.issue_ids:
            counts[issue_id][item.stance] += 1
            mentions[issue_id] += 1

    rows = []
    ordered_issue_ids = [issue_id for issue_id, _ in mentions.most_common() if issue_id != "general"]
    if not ordered_issue_ids:
        ordered_issue_ids = [issue_id for issue_id, _ in mentions.most_common()]

    for issue_id in ordered_issue_ids[:6]:
        count = mentions[issue_id]
        total = count or 1
        rows.append(
            {
                "issue": ISSUE_RULES[issue_id]["label"],
                "mentions": count,
                "positive_pct": round((counts[issue_id]["support"] / total) * 100, 1),
                "negative_pct": round((counts[issue_id]["oppose"] / total) * 100, 1),
                "neutral_pct": round((counts[issue_id]["neutral"] / total) * 100, 1),
            }
        )
    return rows


def _build_issue_source_comparisons(documents: list[PoliticalDocument], issue_stats: list[dict]) -> list[dict]:
    label_to_issue_id = {rule["label"]: issue_id for issue_id, rule in ISSUE_RULES.items()}
    top_labels = [item["issue"] for item in issue_stats if item["issue"] != ISSUE_RULES["general"]["label"]][:3]
    results = []

    for label in top_labels:
        issue_id = label_to_issue_id[label]
        source_counts: dict[str, Counter[str]] = defaultdict(Counter)
        source_labels: dict[str, str] = {}
        mentions: Counter[str] = Counter()

        for item in documents:
            if issue_id not in item.issue_ids:
                continue
            source_counts[item.source.code][item.stance] += 1
            source_labels[item.source.code] = item.source_label
            mentions[item.source.code] += 1

        rows = []
        for source_code, mention_count in mentions.most_common():
            total = mention_count or 1
            rows.append(
                {
                    "source_code": source_code,
                    "source_name": source_labels[source_code],
                    "mentions": mention_count,
                    "support_pct": round((source_counts[source_code]["support"] / total) * 100, 1),
                    "oppose_pct": round((source_counts[source_code]["oppose"] / total) * 100, 1),
                    "neutral_pct": round((source_counts[source_code]["neutral"] / total) * 100, 1),
                }
            )

        results.append({"issue": label, "sources": rows})

    return results


def _build_politician_rankings(
    daily_documents: list[PoliticalDocument], recent_documents: list[PoliticalDocument]
) -> list[dict]:
    counter = Counter()
    source_documents = daily_documents if any(item.mentioned_politicians for item in daily_documents) else recent_documents
    for item in source_documents:
        for name in item.mentioned_politicians:
            counter[name] += 1
    return [{"name": name, "mentions": mentions} for name, mentions in counter.most_common(10)]


def _build_polarization_trend(documents: list[PoliticalDocument], days: int) -> list[dict]:
    by_date: dict[date, Counter[str]] = defaultdict(Counter)
    for item in documents:
        by_date[item.post.created_at.date()][item.stance] += 1

    selected_dates = sorted(by_date.keys())[-days:]
    rows = []
    for item_date in selected_dates:
        total = sum(by_date[item_date].values()) or 1
        rows.append(
            {
                "date": item_date,
                "support_rate": round((by_date[item_date]["support"] / total) * 100, 1),
                "oppose_rate": round((by_date[item_date]["oppose"] / total) * 100, 1),
                "neutral_rate": round((by_date[item_date]["neutral"] / total) * 100, 1),
                "mentions": total,
            }
        )
    return rows


def _build_today_emotion(reference_date: date, documents: list[PoliticalDocument]) -> dict:
    total = len(documents) or 1
    emotion_counts = Counter(item.emotion for item in documents)
    return {
        "date": reference_date,
        "anger_pct": round((emotion_counts["anger"] / total) * 100, 1),
        "positive_pct": round((emotion_counts["positive"] / total) * 100, 1),
        "neutral_pct": round((emotion_counts["neutral"] / total) * 100, 1),
        "mentions": len(documents),
    }


def _build_issue_timeline(documents: list[PoliticalDocument], days: int) -> list[dict]:
    grouped: dict[date, list[PoliticalDocument]] = defaultdict(list)
    for item in documents:
        grouped[item.post.created_at.date()].append(item)

    selected_dates = sorted(grouped.keys())[-days:]
    timeline = []
    for item_date in selected_dates:
        issue_counter = Counter(issue_id for item in grouped[item_date] for issue_id in item.issue_ids)
        issue_id = next(
            (issue for issue, _ in issue_counter.most_common() if issue != "general"),
            issue_counter.most_common(1)[0][0] if issue_counter else "general",
        )
        related_posts = [item for item in grouped[item_date] if issue_id in item.issue_ids]
        representative = max(related_posts, key=lambda item: item.influence_score) if related_posts else max(
            grouped[item_date], key=lambda item: item.influence_score
        )
        timeline.append(
            {
                "date": item_date,
                "issue": ISSUE_RULES[issue_id]["label"],
                "headline": representative.post.title,
                "mentions": issue_counter[issue_id] or len(related_posts),
            }
        )
    return timeline


def _build_hot_posts(documents: list[PoliticalDocument]) -> list[dict]:
    rows = []
    for item in sorted(documents, key=lambda document: document.influence_score, reverse=True)[:8]:
        rows.append(
            {
                "id": item.post.id,
                "source_code": item.source.code,
                "source_name": item.source_label,
                "board_name": item.post.board_name,
                "title": item.post.title,
                "body": item.post.body,
                "created_at": item.post.created_at,
                "view_count": item.post.view_count,
                "upvotes": item.post.upvotes,
                "comment_count": item.post.comment_count,
                "original_url": item.post.original_url,
                "issue_labels": item.issue_labels,
                "stance": item.stance,
                "emotion": item.emotion,
                "influence_score": item.influence_score,
            }
        )
    return rows
