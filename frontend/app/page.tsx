import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { fetchCommunity, fetchDashboardData } from "@/lib/api";
import { fetchKospiFromSkill, fetchNasdaqFromSkill } from "@/lib/skills";

function formatSigned(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

export default async function DashboardPage() {
  const [data, kospi, nasdaqHistory, community] = await Promise.all([
    fetchDashboardData(),
    fetchKospiFromSkill(),
    fetchNasdaqFromSkill(3),
    fetchCommunity({ boardName: "stockus-concept", pageSize: 10 }),
  ]);

  const latest = data.sentiment[0];
  const latestNasdaq = nasdaqHistory[0];
  const summaryLines = [
    `커뮤니티 과열 체감은 ${latest?.hate_index ?? 0} 수준으로 집계됐습니다.`,
    `코스피는 ${kospi?.index_value ?? "-"}, 나스닥 최근 종가는 ${latestNasdaq?.close?.toFixed(2) ?? "-"}입니다.`,
    `오늘 많이 언급된 키워드는 ${latest?.top_keywords.slice(0, 3).join(", ") || "데이터 수집 중"}입니다.`,
  ];

  return (
    <main className="dashboard-page">
      <DomainTabs active="market" />

      <section className="hero-grid">
        <article className="feature-panel">
          <span className="section-label">Market Snapshot</span>
          <div className="headline">
            <div>
              <h1>오늘의 시장 흐름</h1>
              <p>시장 지표와 커뮤니티 반응을 같은 화면에서 비교합니다.</p>
            </div>
            <p>지표와 심리 신호를 함께 보는 대시보드</p>
          </div>

          <div className="market-strip">
            <section className="strip-card strip-card-wide">
              <div>
                <h3>시장 분위기</h3>
                <div className="metric-row">
                  <span>커뮤니티 종합 점수</span>
                  <strong>{latest?.sentiment_score ?? 0}</strong>
                </div>
              </div>
              <div className="strip-meta">
                <span>공포/탐욕 {latest?.fear_greed_score ?? 50}</span>
                <span>혐오 지수 {latest?.hate_index ?? 0}</span>
                <span>불확실성 {latest?.uncertainty_score ?? 0}</span>
              </div>
              <span className="status-badge">Signal Active</span>
            </section>

            <div className="strip-stack">
              <section className="strip-card">
                <div>
                  <h3>나스닥</h3>
                  <div className="metric-row">
                    <span>최근 거래일 {latestNasdaq?.date ?? "-"}</span>
                    <strong>{latestNasdaq?.close?.toFixed(2) ?? "-"}</strong>
                  </div>
                </div>
                <div className="strip-meta">
                  <span>변동 {latestNasdaq ? formatSigned(latestNasdaq.diff) : "-"}</span>
                  <span>등락률 {latestNasdaq ? formatSigned(latestNasdaq.rate) : "-"}%</span>
                </div>
                <span className="status-badge">Skill: Nasdaq</span>
              </section>

              <section className="strip-card">
                <div>
                  <h3>코스피</h3>
                  <div className="metric-row">
                    <span>{kospi?.market_state ?? "-"}</span>
                    <strong>{kospi?.index_value ?? "-"}</strong>
                  </div>
                </div>
                <div className="strip-meta">
                  <span>변동 {kospi?.change_value ?? "-"}</span>
                  <span>등락률 {kospi?.change_percent ?? "-"}%</span>
                </div>
                <span className="status-badge">Skill: KOSPI</span>
              </section>
            </div>
          </div>
        </article>

        <aside className="summary-panel">
          <span className="section-label">3-Line Summary</span>
          <div className="headline compact">
            <div>
              <h2>지금 한눈 요약</h2>
              <p>시장과 커뮤니티 분위기를 빠르게 훑을 수 있게 정리했습니다.</p>
            </div>
          </div>

          <section className="score-box">
            <span>오늘의 경계 레벨</span>
            <strong>{(latest?.hate_index ?? 0) > 40 ? "HIGH" : "WATCH"}</strong>
            <small>감정 지수와 커뮤니티 반응을 합친 요약 카드입니다.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            메인 게시물 목록은 미국주식갤 개념글과 각 글의 혐오지수를 함께 보여줍니다.
          </div>
        </aside>
      </section>

      <section className="feed-panel">
        <span className="section-label">Live Community Feed</span>
        <div className="headline">
          <div>
            <h2>미국주식갤 개념글</h2>
            <p>최신글 대신 개념글을 가져와 제목과 본문 기준 혐오지수, 불확실성, 강세/약세 상태를 같이 보여줍니다.</p>
          </div>
          <p>Live from DCInside</p>
        </div>

        <LiveCommunityFeed
          initialPosts={community.items}
          boardId="stockus"
          boardName="stockus-concept"
          limit={10}
          variant="table"
        />
      </section>

      <section className="lower-grid">
        <ChartPanel
          title="감정 추이"
          data={data.sentiment.map((item) => ({
            label: item.snapshot_date.slice(5),
            value: item.sentiment_score,
          }))}
        />

        <ChartPanel
          title="핵심 키워드"
          color="#285f4b"
          data={data.keywordTrends.map((item) => ({ label: item.keyword, value: item.mentions }))}
        />
      </section>
    </main>
  );
}
