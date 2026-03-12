# 시장 커뮤니티 분석 사이트 소개
# 301호 2팀

## 1. 프로젝트 소개

**Market Signal 허브**는  
뉴스, 시장 데이터, 커뮤니티 반응, 정치 이슈를 한 화면에서 통합적으로 분석할 수 있도록 설계한 플랫폼입니다.

기존에는 경제 흐름을 파악하기 위해 뉴스 사이트, 지표 사이트, 커뮤니티를 각각 따로 확인해야 했습니다.  
저희는 이 과정을 줄이고, **지금 시장 분위기와 개인 투자자 반응을 빠르게 읽을 수 있는 서비스**를 목표로 프로젝트를 개발했습니다.

---

## 2. 프로젝트 목표

- 시장 지표와 커뮤니티 반응을 함께 보여주는 통합 분석 화면 제공
- 경제 뉴스와 커뮤니티 글을 연결해 현재 이슈를 빠르게 파악
- 감정 분석을 통해 불안, 기대, 혐오, 불확실성 같은 정성 데이터를 시각화
- 정치 이슈와 정치 커뮤니티 반응까지 확장해 사회적 분위기와 시장의 연관성 분석

---

## 3. 핵심 기능

### 3-1. 시장 대시보드

- 코스피, 나스닥 등 시장 지표 확인
- 커뮤니티 감정 점수, 공포/탐욕 지수, 혐오지수 확인
- 시장 흐름과 커뮤니티 분위기를 한 화면에서 비교

### 3-2. 뉴스 분석

- 주요 뉴스 기사 수집 및 목록 제공
- 시장 관련 이슈를 빠르게 파악
- 뉴스와 커뮤니티 반응을 함께 해석 가능

### 3-3. 커뮤니티 반응 분석

- 트래픽이 높은 커뮤니티 글 수집
- 게시글의 감정 흐름 분석
- 핵심 키워드와 게시글 반응 수치 표시

### 3-4. 시간대별 비교

- 최근 24시간 기준 커뮤니티 반응 변화 시각화
- 특정 시간대에 감정 변화가 커졌는지 확인
- 시장 변동과 커뮤니티 반응의 연관성 확인

### 3-5. 정치 분석 탭

- 정치 지표, 정치 키워드, 정치 커뮤니티 반응 제공
- 정책 및 정치 이벤트가 여론과 시장에 미치는 영향 확장 분석

---

## 4. 서비스 구성

프로젝트는 크게 두 개의 도메인으로 나뉩니다.

- **Market**
  - 경제 지표
  - 뉴스
  - 커뮤니티 감정 분석
  - 시장 대시보드

- **Politics**
  - 정치 지표
  - 정치 키워드
  - 정치 커뮤니티 분위기
  - 정치 대시보드

---

## 5. 시스템 구조

### Backend

백엔드는 데이터 수집, 저장, 분석, API 제공 역할을 담당합니다.

- `backend/app/api`
  - 시장 관련 API 라우트
- `backend/app/politics/api`
  - 정치 관련 API 라우트
- `backend/app/models`
  - 시장 도메인 DB 모델
- `backend/app/politics/models`
  - 정치 도메인 DB 모델
- `backend/app/collectors`
  - 시장 데이터 및 뉴스 수집기
- `backend/app/politics/collectors`
  - 정치 데이터 수집기
- `backend/app/analytics`
  - 시장 데이터 분석 로직
- `backend/app/politics/analytics`
  - 정치 데이터 분석 로직
- `backend/app/services`
  - 시장 데이터 처리 및 시드 로직
- `backend/app/politics/services`
  - 정치 데이터 처리 및 조회 로직

### Frontend

프론트엔드는 사용자에게 데이터를 시각적으로 보여주는 역할을 담당합니다.

- `frontend/app/page.tsx`
  - 시장 메인 대시보드
- `frontend/app/politics/page.tsx`
  - 정치 대시보드
- `frontend/app/news/page.tsx`
  - 뉴스 목록 화면
- `frontend/app/community/page.tsx`
  - 커뮤니티 목록 및 분석 화면

---

## 6. 발표 시연 흐름

발표에서는 아래 순서로 보여주면 자연스럽습니다.

1. **메인 화면 소개**
   - 시장 데이터와 커뮤니티 반응을 통합해서 보여주는 서비스임을 설명

2. **시장 대시보드 시연**
   - 코스피, 나스닥, 감정 점수, 혐오지수 확인
   - 시장 숫자와 커뮤니티 반응을 함께 보여준다는 점 강조

3. **커뮤니티 분석 시연**
   - 실제 게시글 기반으로 어떤 키워드가 많이 언급되는지 설명
   - 감정 분석 결과가 어떻게 표시되는지 보여주기

4. **시간대별 비교 설명**
   - 최근 24시간 반응 변화와 시장 변동 관계 설명

5. **정치 탭 소개**
   - 경제 외에도 정치 이슈와 커뮤니티 반응을 분석할 수 있음을 설명

6. **마무리**
   - 단순 조회 서비스가 아니라 의사결정 보조용 분석 플랫폼이라는 점 강조

---

## 7. 실행 방법

### 7-1. Docker 실행

환경 파일 복사:

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.local.example frontend\.env.local
```

전체 실행:

```powershell
docker compose up --build
```

### 7-2. 로컬 실행

#### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
uvicorn app.main:app --reload
```

#### Frontend

```powershell
cd frontend
npm install
npm run dev
```

### 7-3. 실행 확인 주소

- 프론트 메인: `http://localhost:3000`
- 정치 탭: `http://localhost:3000/politics`
- 뉴스 탭: `http://localhost:3000/news`
- 커뮤니티 탭: `http://localhost:3000/community`
- 백엔드 헬스체크: `http://localhost:8000/health`

---

## 8. 주요 API

### Market API

- `GET /health`
- `GET /api/v1/indicators/latest`
- `GET /api/v1/news`
- `GET /api/v1/community/posts`
- `GET /api/v1/analytics/daily-sentiment`
- `GET /api/v1/analytics/keyword-trends`

### Politics API

- `GET /api/v1/politics/dashboard`
- `GET /api/v1/politics/politicians`
- `GET /api/v1/politics/keywords`
- `GET /api/v1/politics/community-posts`
- `GET /api/v1/politics/sentiment`

---

## 9. 데이터 및 분석 방식

- 시장 지표 데이터 수집
- 뉴스 데이터 수집 및 요약
- 커뮤니티 게시글 수집
- 게시글 기반 감정 분석
- 키워드 추출 및 트렌드 시각화
- 정치 데이터와 시장 데이터의 확장 연계 분석

---

## 10. 준수 사항

커뮤니티 및 외부 데이터 수집 시 아래 원칙을 따릅니다.

- 공식 API, RSS, 공개 데이터 우선 사용
- `robots.txt`, 이용약관, 요청 빈도 제한 준수
- 권한이 불명확한 수집 대상은 비활성화 또는 목업 상태 유지

---

## 11. 향후 개선 방향

- 실시간 데이터 연동 강화
- 감정 분석 정확도 고도화
- 더 다양한 커뮤니티 및 뉴스 소스 확장
- 투자 의사결정을 보조하는 종합 분석 플랫폼으로 발전

---

## 12. 한 줄 정리

**Market Signal Hub는 뉴스, 시장 지표, 커뮤니티 반응, 정치 이슈를 통합해  
현재 분위기를 빠르게 읽을 수 있도록 만든 데이터 분석 플랫폼입니다.**
