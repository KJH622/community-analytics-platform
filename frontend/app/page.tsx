import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { MarketComparisonChart } from "@/components/market-comparison-chart";
import { MetricCard } from "@/components/metric-card";
import { fetchCommunity, fetchDashboardData, fetchMarketComparison } from "@/lib/api";

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value == null) {
    return "-";
  }
  return value.toFixed(digits);
}

function formatSignedPercent(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export default async function DashboardPage() {
  const [data, community, market] = await Promise.all([
    fetchDashboardData(),
    fetchCommunity({ topicCategory: "economy", pageSize: 8 }),
    fetchMarketComparison(14),
  ]);

  const latest = data.sentiment[0] ?? null;
  const latestIndicator = data.indicators.find((item) => item.latest_release) ?? null;
  const topKeywords = latest?.top_keywords?.slice(0, 4).join(", ") || "데이터 집계 중";
  const summaryLines = [
    `경제 커뮤니티 종합 감정 점수는 ${formatNumber(latest?.sentiment_score)}입니다.`,
    `현재 혐오지수는 ${formatNumber(market.latest.hate_index)}이며 전일 대비 ${formatNumber(market.latest.hate_change)}p 변화했습니다.`,
    `오늘 많이 언급된 키워드는 ${topKeywords} 입니다.`,
  ];

  return (
    <main className="dashboard-page">
      <DomainTabs active="market" />

      <section className="hero-grid">
        <article className="feature-panel">
          <span className="section-label">경제 대시보드</span>
          <div className="headline">
            <div>
              <h1>경제 커뮤니티와 시장 흐름</h1>
              <p>저장된 경제 게시글 감정과 실제 한국 시장 지표를 한 화면에서 같이 봅니다.</p>
            </div>
            <p>크롤링과 집계는 1시간 주기로 갱신됩니다.</p>
          </div>

          <div className="card-grid">
            <MetricCard
              label="코스피"
              value={formatNumber(market.latest.kospi_close, 2)}
              caption={`전일 대비 ${formatSignedPercent(market.latest.kospi_change_pct)}`}
            />
            <MetricCard
              label="코스닥"
              value={formatNumber(market.latest.kosdaq_close, 2)}
              caption={`전일 대비 ${formatSignedPercent(market.latest.kosdaq_change_pct)}`}
            />
            <MetricCard
              label="경제 혐오지수"
              value={formatNumber(market.latest.hate_index, 2)}
              caption={`전일 대비 ${formatNumber(market.latest.hate_change, 2)}p`}
            />
            <MetricCard
              label="최신 경제 지표"
              value={latestIndicator?.latest_release?.actual_value?.toString() ?? "-"}
              caption={latestIndicator ? `${latestIndicator.name} (${latestIndicator.country})` : "표시할 지표가 아직 없습니다."}
            />
          </div>
        </article>

        <aside className="summary-panel">
          <span className="section-label">오늘 요약</span>
          <div className="headline compact">
            <div>
              <h2>경제 분위기 한눈에 보기</h2>
              <p>경제 커뮤니티 반응과 시장 흐름을 빠르게 읽을 수 있도록 정리했습니다.</p>
            </div>
          </div>

          <section className="score-box">
            <span>경계 수준</span>
            <strong>{(latest?.hate_index ?? 0) >= 40 ? "높음" : "관찰"}</strong>
            <small>감정 급등 여부를 가장 빠르게 확인하는 보조 지표입니다.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            아래 비교 그래프는 코스피, 코스닥, 혐오지수를 같은 구간에서 0~100으로 정규화해 추세 유사성을 보기 쉽게 만든 것입니다.
          </div>
        </aside>
      </section>

      <section className="panel">
        <div className="headline">
          <div>
            <h2>코스피 · 코스닥 · 혐오지수 추세 비교</h2>
            <p>세 지표를 한 그래프에서 정규화해서 움직임이 비슷한지 비교합니다.</p>
          </div>
          <p>{market.comparison_basis}</p>
        </div>
        <MarketComparisonChart data={market.points} />
      </section>

      <section className="feed-panel">
        <span className="section-label">경제 커뮤니티 글</span>
        <div className="headline">
          <div>
            <h2>최신 경제 게시글</h2>
            <p>크롤 서버가 저장한 경제 게시글을 바로 보여줍니다.</p>
          </div>
          <p>누적 {community.total}건</p>
        </div>

        <LiveCommunityFeed initialPosts={community.items} topicCategory="economy" limit={8} variant="table" />
      </section>

      <section className="lower-grid">
        <ChartPanel
          title="경제 감정 추이"
          data={data.sentiment.map((item) => ({
            label: item.snapshot_date.slice(5),
            value: item.sentiment_score,
          }))}
        />

        <ChartPanel
          title="핵심 키워드 추이"
          color="#285f4b"
          data={data.keywordTrends.map((item) => ({ label: item.keyword, value: item.mentions }))}
        />
      </section>
    </main>
  );
}
