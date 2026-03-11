# API Design

## Market APIs

- `GET /health`
- `GET /api/v1/indicators/latest`
- `GET /api/v1/indicators/{indicator_code}/history`
- `GET /api/v1/news`
- `GET /api/v1/news/{id}`
- `GET /api/v1/community/posts`
- `GET /api/v1/community/posts/{id}`
- `GET /api/v1/analytics/daily-sentiment`
- `GET /api/v1/analytics/keyword-trends`
- `GET /api/v1/analytics/topic-breakdown`
- `POST /api/v1/jobs/run/{job_name}`

## Politics APIs

- `GET /api/v1/politics/dashboard`
  - 정치 탭 초기 로딩용 집계 응답
  - 포함 항목: 최신 스냅샷, 정치 지표, 정치인 언급량, 키워드 트렌드, 인기글, 참고 커뮤니티
- `GET /api/v1/politics/politicians`
- `GET /api/v1/politics/politicians/{name}`
- `GET /api/v1/politics/indicators`
- `GET /api/v1/politics/keywords`
- `GET /api/v1/politics/community-posts`
- `GET /api/v1/politics/sentiment`
- `GET /api/v1/politics/polarization`

## 잡 실행 API

- `POST /api/v1/jobs/run/collect_indicators`
- `POST /api/v1/jobs/run/collect_news`
- `POST /api/v1/jobs/run/collect_mock_community`
- `POST /api/v1/jobs/run/compute_daily_snapshots`
- `POST /api/v1/jobs/run/collect_political_indicators`
- `POST /api/v1/jobs/run/collect_political_posts`
- `POST /api/v1/jobs/run/compute_political_daily_snapshots`
