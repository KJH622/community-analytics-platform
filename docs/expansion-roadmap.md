# Expansion Roadmap

## LLM 기반 감성 분석

- 현재 규칙 기반 분석 모듈은 `AnalysisEngine` 인터페이스 뒤에 있습니다.
- 향후 LLM 분석기를 붙일 때는 `app/analytics/base.py`를 구현해 교체하거나 앙상블로 확장합니다.
- 전략:
  - 문서 길이 제한 및 chunking
  - label schema 고정
  - human review set으로 품질 검증
  - 모델 출력 캐싱

## Kafka 또는 큐 기반 확장

- 현재는 APScheduler가 프로세스 내부에서 작업을 실행합니다.
- 수집량이 커지면:
  - collector -> queue publish
  - worker -> normalize/store/analyze
  - snapshot worker -> daily aggregate
- 장점:
  - 재시도 분리
  - backpressure 대응
  - 소스별 병렬 처리

## OpenSearch 도입 시

- `articles`, `community_posts` 본문 검색을 PostgreSQL FTS에서 OpenSearch 인덱스로 분리합니다.
- 변경점:
  - ingest 후 search index sync worker 추가
  - API 검색 레이어 분리
  - relevance ranking 및 aggregations 개선

## Airflow 도입 시

- `jobs/registry.py`의 작업 정의를 DAG 단위로 이관합니다.
- 스케줄, 의존성, 재실행, 백필 관리가 쉬워집니다.
- 초기 MVP는 APScheduler가 간단하고 운영 부담이 적습니다.

## 법적, 윤리적, 운영적 주의사항

- 뉴스 전문 저장은 라이선스 범위를 검토해야 합니다.
- 커뮤니티 데이터는 약관과 robots 정책을 준수해야 하며, 작성자 정보는 해시 처리나 최소 보관 원칙을 적용합니다.
- 혐오/비하 사전은 연구/모더레이션 목적이며, 직접 노출을 최소화하고 접근 통제를 권장합니다.
- 투자 의사결정 지표는 설명 가능성과 검증 리포트를 함께 제공해야 합니다.
