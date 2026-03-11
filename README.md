# market-signal-hub

경제 데이터, 뉴스, 커뮤니티 여론을 통합 수집하고 규칙 기반 분석으로 시장 정서를 보여주는 MVP 시스템입니다.

## 프로젝트 개요

- 경제 지표 수집: BLS CPI/실업률, FRED 기반 시장 시계열 예시
- 뉴스 수집: RSS 우선 수집, 중복 제거, 기사 클러스터링 초안 지원
- 커뮤니티 수집: 법적/약관 리스크를 고려한 플러그인 구조와 안전한 mock 커넥터 제공
- 분석: 감성, 공포/탐욕, 혐오, 불확실성, 시장 방향성, 키워드 추출
- 정치 분석: 정치 게시글, 정치인 언급량, 지지율/정당 지표, 정치 감정/양극화/선거 관심도
- 서빙: FastAPI API + Next.js 대시보드
- 운영: APScheduler, Docker Compose, Alembic, pytest, ruff, black

## 아키텍처

수집 계층은 `backend/app/collectors`에 있고, 소스별 커넥터가 정규화된 문서 DTO를 반환합니다.  
정제 계층은 텍스트 정리와 해시/정규화 로직을 담당합니다.  
분석 계층은 규칙 기반 점수 계산과 일별 스냅샷 집계를 수행합니다.  
저장 계층은 PostgreSQL과 SQLAlchemy 모델로 raw/clean/analytics 성격의 데이터를 구분해 저장합니다.  
서빙 계층은 FastAPI REST API와 Next.js 대시보드로 구성됩니다.

자세한 설계는 [docs/architecture.md](/Users/user/Desktop/pj/docs/architecture.md)와 [docs/expansion-roadmap.md](/Users/user/Desktop/pj/docs/expansion-roadmap.md)에 정리되어 있습니다.
정치 모듈 설계는 [docs/politics-architecture.md](/Users/user/Desktop/pj/docs/politics-architecture.md), 데이터 모델은 [docs/data-model.md](/Users/user/Desktop/pj/docs/data-model.md)에 있습니다.

## 디렉토리 구조

```text
market-signal-hub/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ analytics/
│  │  ├─ collectors/
│  │  ├─ core/
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ politics/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ jobs/
│  │  ├─ utils/
│  │  └─ fixtures/
│  ├─ alembic/
│  └─ tests/
├─ frontend/
├─ docs/
├─ scripts/
├─ docker-compose.yml
└─ .env.example
```

## 빠른 시작

### 1. 환경변수 준비

```bash
cp .env.example .env
```

### 2. Docker Compose로 실행

```bash
docker compose up --build
```

실행 후:

- API 문서: [http://localhost:8000/docs](http://localhost:8000/docs)
- 프론트엔드: [http://localhost:3000](http://localhost:3000)

### 3. 로컬 개발

백엔드:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload
```

프론트엔드:

```bash
cd frontend
npm install
npm run dev
```

## 테스트

백엔드 테스트:

```bash
cd backend
uv run pytest
```

## 수집 소스 정책

- 공식 API 또는 공개 RSS를 우선 사용합니다.
- robots.txt, 서비스 약관, 요청 빈도 제한을 지키지 못하는 커뮤니티는 구현을 비활성화된 커넥터 인터페이스 수준에서만 제공합니다.
- 커뮤니티 작성자 식별자는 저장 시 해시 처리합니다.
- 민감 표현 사전은 [backend/app/analytics/lexicons/hate_terms.txt](/Users/user/Desktop/pj/backend/app/analytics/lexicons/hate_terms.txt)에 분리합니다.
- 정치 커뮤니티는 기본적으로 mock/disabled 구조로 제공하며, 실사이트 활성화 전 법적 검토가 필수입니다.

## 새 커넥터 추가 방법

1. `backend/app/collectors/...` 하위에 새 커넥터 클래스를 추가합니다.
2. `BaseCollector` 또는 `BaseCommunityConnector`를 상속합니다.
3. `normalize_*` 메서드에서 공통 DTO로 변환합니다.
4. `backend/app/jobs/registry.py`에 수집 작업을 등록합니다.
5. 약관/robots 정책과 rate limit 문서를 업데이트합니다.

## 주의사항

- 이 프로젝트는 투자 자문이 아닌 데이터 분석용 예제입니다.
- 뉴스 전문과 커뮤니티 데이터는 해당 서비스의 라이선스/약관 범위 내에서만 저장 및 활용해야 합니다.
- DCInside 등 일부 사이트는 실제 크롤러 대신 비활성 커넥터와 mock 예시만 제공합니다.
