# Politics Architecture

## 분리 원칙

- 정치 분석은 `backend/app/politics` 아래에 별도 모듈로 구현합니다.
- 정치 데이터는 경제/시장 문서와 섞지 않고 별도 테이블을 사용합니다.
- 공통 인프라만 공유합니다.
  - FastAPI 앱
  - DB 세션
  - `sources`, `source_connectors`, `ingestion_jobs`, `ingestion_logs`

## 정치 데이터 흐름

1. `politics.collectors`가 fixture 기반 정치 게시글/지표를 정규화합니다.
2. `politics.services.storage`가 `political_posts`, `political_indicators`, `political_indicator_values`에 저장합니다.
3. `politics.analytics.rule_based`가 정치 감정과 양극화 지표를 계산합니다.
4. 결과는 `political_sentiment`, `political_entities`, `political_daily_snapshot`에 저장됩니다.
5. `politics.api.routes`가 정치 탭 전용 REST API를 제공합니다.
6. 프론트엔드는 `Politics` 탭에서 오직 정치 API만 사용합니다.

## 커넥터 정책

- 실데이터 커뮤니티는 `DisabledPoliticalCommunityConnector`로 먼저 등록합니다.
- robots.txt, 이용약관, 요청 빈도 정책을 검토한 뒤에만 활성화합니다.
- 현재 MVP는 `MockPoliticalCommunityConnector`, `MockPoliticalIndicatorCollector`만 실행 가능하게 둡니다.
