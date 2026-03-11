# Architecture

## 목표

`market-signal-hub`는 경제 지표, 뉴스, 커뮤니티 텍스트를 통합 수집하고 정제/분석하여 API와 대시보드로 제공하는 시스템입니다.

## 계층 분리

### 1. Collect

- `collectors/indicators`: 공식 API 또는 신뢰 가능한 공개 시계열에서 경제 지표/시장 데이터를 수집
- `collectors/news`: RSS 우선, 필요 시 허용된 범위 내에서 기사 본문 보강
- `collectors/communities`: 안전한 커넥터 인터페이스와 mock/disabled 구현

### 2. Clean

- `services/text_cleaner.py`: HTML 제거, 공백 정리, URL/이모지 정규화
- `utils/hashing.py`: 본문 해시, 작성자 해시, 중복 방지 키 생성

### 3. Analyze

- `analytics/rule_based.py`: sentiment_score, fear_greed_score, hate_index, uncertainty_score, market_bias
- `analytics/keywords.py`: 빈도 기반 키워드 추출
- `analytics/snapshots.py`: 일별 시장 정서 스냅샷 계산
- `politics/analytics/rule_based.py`: 정치 감정, 양극화, 선거 관심도 계산

### 4. Store

- `models/`: SQLAlchemy ORM
- Raw 성격 데이터: 원문 JSON, source payload, fetch metadata
- Clean 성격 데이터: 정규화된 기사/커뮤니티 글
- Analytics 성격 데이터: sentiment, snapshot, tags, clusters

### 5. Serve

- `api/routes`: REST API
- `politics/api/routes.py`: 정치 탭 전용 REST API
- `frontend/`: 대시보드 및 필터 UI

## 데이터 흐름

1. 스케줄러가 수집 작업을 실행합니다.
2. 각 수집기는 외부 소스에서 문서를 가져와 공통 DTO로 정규화합니다.
3. 정제 서비스가 텍스트 정리, 작성자 해시화, canonical URL 보정을 수행합니다.
4. 저장 서비스가 중복 검사 후 DB에 upsert합니다.
5. 분석 서비스가 문서별 sentiment와 키워드를 계산하고 저장합니다.
6. 스냅샷 작업이 일별 지수를 계산합니다.
7. API가 시계열/검색/집계 데이터를 제공합니다.
8. 정치 모듈은 별도 API와 별도 테이블에서 동일한 흐름으로 처리됩니다.
9. 프론트엔드가 API를 호출해 카드, 차트, 리스트를 렌더링합니다.

## 확장 전략

- 수집량 증가 시 Kafka나 Redis 큐로 ingestion 비동기화
- 텍스트 분석 고도화 시 LLM 또는 임베딩 모델 교체
- 검색 요구 증가 시 PostgreSQL FTS에서 OpenSearch로 분리
- 배치 오케스트레이션이 커지면 APScheduler에서 Airflow로 이전

## 커뮤니티 수집 정책

- 실제 구현 전 반드시 robots.txt와 서비스 약관을 검토해야 합니다.
- 허용 여부가 불명확하거나 금지 조항이 있으면 수집기는 `disabled` 상태로 둡니다.
- 기본 제공 `DcInsideConnector`는 비활성 상태 예시이며, `MockCommunityConnector`만 즉시 실행 가능합니다.
