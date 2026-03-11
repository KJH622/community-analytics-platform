# Data Model

## 공통/시장 영역

### `sources`
- 목적: 외부 데이터 소스의 메타데이터 저장
- 주요 컬럼: `code`, `name`, `kind`, `country`, `base_url`, `enabled`, `robots_policy`, `tos_notes`
- 인덱스/유니크: `code` unique, `kind`, `country`

### `source_connectors`
- 목적: 소스별 커넥터 설정과 상태
- 주요 컬럼: `source_id`, `connector_type`, `status`, `schedule_hint`, `rate_limit_per_minute`
- 인덱스/유니크: `(source_id, connector_type)` unique

### `economic_indicators`
- 목적: 경제 지표 메타데이터
- 주요 컬럼: `code`, `name`, `country`, `category`, `unit`, `frequency`, `source_url`
- 인덱스/유니크: `code` unique

### `indicator_releases`
- 목적: 지표 발표/관측치 저장
- 주요 컬럼: `indicator_id`, `country`, `release_date`, `release_time`, `actual_value`, `forecast_value`, `previous_value`, `unit`, `importance`, `source_url`
- 인덱스/유니크: `(indicator_id, release_date)` unique

### `articles`
- 목적: 뉴스 기사 원문/정제본 저장
- 주요 컬럼: `source_id`, `cluster_id`, `title`, `summary`, `body`, `published_at`, `canonical_url`, `content_hash`, `raw_payload`
- 인덱스/유니크: `(source_id, canonical_url)` unique, `published_at`

### `article_clusters`
- 목적: 유사 기사 클러스터
- 주요 컬럼: `cluster_key`, `topic`, `representative_title`, `centroid_terms`
- 인덱스/유니크: `cluster_key` unique

### `community_posts`
- 목적: 경제 커뮤니티 게시글 저장
- 주요 컬럼: `source_id`, `board_name`, `external_id`, `title`, `body`, `published_at`, `author_hash`, `view_count`, `upvotes`, `downvotes`, `comment_count`, `url`
- 인덱스/유니크: `(source_id, external_id)` unique, `published_at`

### `community_comments`
- 목적: 커뮤니티 댓글 저장
- 주요 컬럼: `post_id`, `external_id`, `body`, `published_at`, `author_hash`
- 인덱스/유니크: `(post_id, external_id)` unique

### `entities`
- 목적: 경제/시장 개체 기준 테이블
- 주요 컬럼: `entity_type`, `name`, `canonical_name`, `symbol`
- 인덱스: `(entity_type, canonical_name)`

### `topics`
- 목적: 주제 분류 기준 테이블
- 주요 컬럼: `code`, `name`, `description`, `keywords`
- 인덱스/유니크: `code` unique

### `sentiments`
- 목적: 문서별 규칙 기반 분석 결과
- 주요 컬럼: `document_type`, `document_id`, `sentiment_score`, `fear_greed_score`, `hate_index`, `uncertainty_score`, `market_bias`, `labels`, `keywords`
- 인덱스/유니크: `(document_type, document_id)` unique

### `document_tags`
- 목적: keyword/topic/entity 태그 저장
- 주요 컬럼: `document_type`, `document_id`, `tag_type`, `tag_value`, `score`
- 인덱스: `(document_type, document_id)`, `(tag_type, tag_value)`

### `ingestion_jobs`
- 목적: 수집 작업 실행 단위 저장
- 주요 컬럼: `job_name`, `source_id`, `status`, `triggered_by`, `items_seen`, `items_written`, `items_skipped`, `error_summary`
- 인덱스: `job_name`

### `ingestion_logs`
- 목적: 작업 로그 이벤트 저장
- 주요 컬럼: `job_id`, `level`, `message`, `context`
- 인덱스: `job_id`

### `daily_market_sentiment_snapshots`
- 목적: 일별 시장 정서 스냅샷
- 주요 컬럼: `snapshot_key`, `snapshot_date`, `source_kind`, `country`, `topic_code`, `sentiment_avg`, `fear_greed_avg`, `hate_index_avg`, `uncertainty_avg`, `bullish_ratio`, `bearish_ratio`, `neutral_ratio`, `top_keywords`
- 인덱스/유니크: `snapshot_key` unique, `snapshot_date`

## 정치 영역

### `political_parties`
- 목적: 정당 기준 정보
- 주요 컬럼: `name`, `ideology`, `country`, `description`
- 인덱스/유니크: `name` unique

### `politicians`
- 목적: 정치인 기준 정보
- 주요 컬럼: `name`, `party`, `party_id`, `position`, `ideology`, `country`, `start_term`, `end_term`
- 인덱스: `(name, country)`

### `political_indicators`
- 목적: 정치 지표 메타데이터
- 주요 컬럼: `code`, `indicator_name`, `country`, `unit`, `source`, `description`
- 인덱스/유니크: `code` unique

### `political_indicator_values`
- 목적: 정치 지표 시계열 값
- 주요 컬럼: `indicator_id`, `date`, `value`, `label`, `source`, `unit`
- 인덱스/유니크: `(indicator_id, date, label)` unique

### `political_topics`
- 목적: 정치 주제 분류 기준
- 주요 컬럼: `code`, `name`, `description`, `keywords`
- 인덱스/유니크: `code` unique

### `political_posts`
- 목적: 정치 커뮤니티 게시글 저장
- 주요 컬럼: `source_id`, `community_name`, `board_name`, `external_id`, `title`, `body`, `published_at`, `view_count`, `upvotes`, `comment_count`, `url`
- 인덱스/유니크: `(source_id, external_id)` unique, `published_at`

### `political_sentiment`
- 목적: 정치 게시글 감정/양극화 분석 결과
- 주요 컬럼: `post_id`, `political_sentiment_score`, `support_score`, `opposition_score`, `anger_score`, `sarcasm_score`, `apathy_score`, `enthusiasm_score`, `political_polarization_index`, `election_heat_index`, `labels`, `keywords`
- 인덱스/유니크: `post_id` unique

### `political_entities`
- 목적: 정치인/정당/정책 키워드 개체 추출
- 주요 컬럼: `post_id`, `entity_type`, `name`, `canonical_name`, `mention_count`, `score`
- 인덱스: `(entity_type, name)`, `post_id`

### `political_daily_snapshot`
- 목적: 정치 일별 스냅샷
- 주요 컬럼: `snapshot_date`, `political_sentiment_avg`, `political_polarization_index`, `election_heat_index`, `top_keywords`, `top_politicians`, `post_count`
- 인덱스/유니크: `snapshot_date` unique
