import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { HourlyComparisonPanel } from "@/components/hourly-comparison-panel";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { fetchCommunity, fetchDashboardData, fetchMarketSummary } from "@/lib/api";
import { fetchKospiFromSkill, fetchKospiHistoryFromSkill, fetchNasdaqFromSkill } from "@/lib/skills";

const TEXT = {
  heroTitle: "\uC624\uB298\uC758 \uC2DC\uC7A5 \uD750\uB984",
  heroBody: "\uC2DC\uC7A5 \uC9C0\uD45C\uC640 \uCEE4\uBBA4\uB2C8\uD2F0 \uBC18\uC751\uC744 \uD55C \uD654\uBA74\uC5D0\uC11C \uBE44\uAD50\uD569\uB2C8\uB2E4.",
  heroAside: "\uC9C0\uD45C\uC640 \uC2EC\uB9AC \uC2E0\uD638\uB97C \uD568\uAED8 \uBCF4\uB294 \uB300\uC2DC\uBCF4\uB4DC",
  moodTitle: "\uC2DC\uC7A5 \uBD84\uC704\uAE30",
  sentimentLabel: "\uC2DC\uC7A5 \uC2EC\uB9AC \uC885\uD569 \uC810\uC218",
  fearGreedLabel: "\uACF5\uD3EC/\uD0D0\uC695",
  hateLabel: "\uCEE4\uBBA4\uB2C8\uD2F0 \uC801\uB300\uAC10 \uC9C0\uC218",
  hourlyHateLabel: "\uCD5C\uADFC 1\uC2DC\uAC04 \uD3C9\uADE0 \uD610\uC624\uC9C0\uC218",
  uncertaintyLabel: "\uBD88\uD655\uC2E4\uC131",
  toneLabel: "\uC624\uB298\uC758 \uC2DC\uC7A5 \uCCB4\uAC10",
  toneBody: "\uD610\uC624\uC9C0\uC218\uB97C \uD3EC\uD568\uD55C \uCEE4\uBBA4\uB2C8\uD2F0 \uC2EC\uB9AC\uC640 \uC9C0\uC218 \uD750\uB984\uC744 \uD568\uAED8 \uC77D\uC740 \uACB0\uACFC\uC785\uB2C8\uB2E4.",
  nasdaqTitle: "\uB098\uC2A4\uB2E5",
  nasdaqDate: "\uCD5C\uADFC \uAC70\uB798\uC77C",
  kospiTitle: "\uCF54\uC2A4\uD53C",
  changeLabel: "\uBCC0\uB3D9",
  rateLabel: "\uB4F1\uB77D\uB960",
  nasdaqChart: "\uB098\uC2A4\uB2E5 7\uC77C \uD750\uB984",
  kospiChart: "\uCF54\uC2A4\uD53C 7\uC77C \uD750\uB984",
  summaryTitle: "\uC9C0\uAE08 \uD55C\uB208 \uC694\uC57D",
  summaryBody: "\uC2DC\uC7A5\uACFC \uCEE4\uBBA4\uB2C8\uD2F0 \uBD84\uC704\uAE30\uB97C \uBE60\uB974\uAC8C \uD6D1\uC744 \uC218 \uC788\uAC8C \uC815\uB9AC\uD588\uC2B5\uB2C8\uB2E4.",
  riskTitle: "\uC624\uB298\uC758 \uACBD\uACC4 \uB808\uBCA8",
  sourceGpt: "\uBD84\uC11D \uCD9C\uCC98: GPT \uC694\uC57D",
  sourceFallback: "\uBD84\uC11D \uCD9C\uCC98: \uAE30\uBCF8 \uADDC\uCE59 \uAE30\uBC18 \uC694\uC57D",
  note: "\uBA54\uC778 \uAC8C\uC2DC\uBB3C \uBAA9\uB85D\uC740 \uBBF8\uAD6D\uC8FC\uC2DD \uAC24\uB7EC\uB9AC \uAC8C\uC2DC\uAE00\uACFC \uAC01 \uAE00\uC758 \uD610\uC624\uC9C0\uC218\uB97C \uD568\uAED8 \uBCF4\uC5EC\uC90D\uB2C8\uB2E4.",
  weekNote: "\uCD5C\uADFC 24\uC2DC\uAC04 \uBBF8\uC8FC\uAC24 \uAC1C\uB150\uAE00 GPT \uBD84\uC11D \uD3C9\uADE0\uAC12 \uAE30\uC900",
  feedTitle: "\uBBF8\uAD6D\uC8FC\uC2DD \uAC1C\uB150\uAE00",
  feedBody: "\uCD5C\uC2E0 \uAC8C\uC2DC\uAE00\uC758 \uC81C\uBAA9\uACFC \uBCF8\uBB38 \uAE30\uC900 \uD610\uC624\uC9C0\uC218, \uBD88\uD655\uC2E4\uC131, \uAC15\uC138/\uC57D\uC138 \uC2E0\uD638\uB97C \uD568\uAED8 \uBCF4\uC5EC\uC90D\uB2C8\uB2E4.",
  sentimentChart: "\uAC10\uC815 \uCD94\uC774",
  keywordChart: "\uD575\uC2EC \uD0A4\uC6CC\uB4DC",
  fallbackNote: "\uC694\uC57D API \uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD574 \uAE30\uBCF8 \uBB38\uC7A5\uC73C\uB85C \uD45C\uC2DC \uC911\uC785\uB2C8\uB2E4.",
  fallbackLine1: "\uCEE4\uBBA4\uB2C8\uD2F0 \uD610\uC624\uC9C0\uC218\uB294",
  fallbackLine2: "\uCF54\uC2A4\uD53C\uB294",
  fallbackLine3: "\uC8FC\uC694 \uD0A4\uC6CC\uB4DC\uB294",
  collecting: "\uB370\uC774\uD130 \uC218\uC9D1 \uC911",
};

function formatSigned(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function parseMaybeNumber(value: number | string | null | undefined) {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value.replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export default async function DashboardPage() {
  const [data, kospi, kospiHistory, nasdaqHistory, community] = await Promise.all([
    fetchDashboardData(),
    fetchKospiFromSkill(),
    fetchKospiHistoryFromSkill(7),
    fetchNasdaqFromSkill(7),
    fetchCommunity({ boardName: "stockus-concept", pageSize: 10 }),
  ]);

  const latest = data.sentiment[0];
  const communityOverview = data.communityOverview;
  const latestNasdaq = nasdaqHistory[0];
  const marketSummary = await fetchMarketSummary({
    sentiment_score: communityOverview.sentiment_score,
    fear_greed_score: communityOverview.fear_greed_score,
    hate_index: communityOverview.hate_index,
    uncertainty_score: communityOverview.uncertainty_score,
    top_keywords: communityOverview.top_keywords,
    kospi_value: parseMaybeNumber(kospi?.index_value),
    kospi_change_percent: parseMaybeNumber(kospi?.change_percent),
    kospi_state: kospi?.market_state ?? null,
    nasdaq_value: latestNasdaq?.close ?? null,
    nasdaq_change_percent: latestNasdaq?.rate ?? null,
    nasdaq_trade_date: latestNasdaq?.date ?? null,
    post_count: communityOverview.post_count,
  }).catch(() => ({
    status_label: communityOverview.hate_index >= 40 ? "HIGH" : "WATCH",
    summary_lines: [
      `${TEXT.fallbackLine1} ${communityOverview.hate_index.toFixed(1)}\uB85C \uC9D1\uACC4\uB410\uC2B5\uB2C8\uB2E4.`,
      `${TEXT.fallbackLine2} ${kospi?.index_value ?? "-"}, \uB098\uC2A4\uB2E5\uC740 ${latestNasdaq?.close?.toFixed(2) ?? "-"}\uC785\uB2C8\uB2E4.`,
      `${TEXT.fallbackLine3} ${communityOverview.top_keywords.slice(0, 3).join(", ") || TEXT.collecting}\uC785\uB2C8\uB2E4.`,
    ],
    analysis_note: TEXT.fallbackNote,
    source: "fallback",
  }));

  const sentimentScore = communityOverview.sentiment_score;
  const fearGreedScore = communityOverview.fear_greed_score;
  const hateIndex = communityOverview.hate_index;
  const uncertaintyScore = communityOverview.uncertainty_score;
  const latestHourlyHatePoint = data.hourlyComparison.points
    .slice()
    .reverse()
    .find((point) => point.hate_index !== null);
  const recentHourlyAverageHateIndex = latestHourlyHatePoint?.hate_index ?? 0;

  return (
    <main className="dashboard-page">
      <DomainTabs active="market" />

      <section className="hero-grid">
        <article className="feature-panel">
          <span className="section-label">Market Snapshot</span>
          <div className="headline">
            <div>
              <h1>{TEXT.heroTitle}</h1>
              <p>{TEXT.heroBody}</p>
            </div>
            <p>{TEXT.heroAside}</p>
          </div>

          <div className="market-strip">
            <section className="strip-card strip-card-wide">
              <div>
                <h3>{TEXT.moodTitle}</h3>
                <div className="metric-row">
                  <span>{TEXT.sentimentLabel}</span>
                  <strong>{sentimentScore.toFixed(1)}</strong>
                </div>
              </div>
              <div className="strip-meta">
                <span>{TEXT.fearGreedLabel} {fearGreedScore.toFixed(1)}</span>
                <span>{TEXT.hateLabel} {hateIndex.toFixed(1)}</span>
                <span>{TEXT.hourlyHateLabel} {recentHourlyAverageHateIndex.toFixed(1)}</span>
                <span>{TEXT.uncertaintyLabel} {uncertaintyScore.toFixed(1)}</span>
              </div>
              <div className="market-tone-box">
                <span className="market-tone-label">{TEXT.toneLabel}</span>
                <strong>{marketSummary.status_label}</strong>
                <p>{TEXT.toneBody}</p>
                <small>{TEXT.weekNote}</small>
              </div>
              <span className="status-badge">Signal Active</span>
            </section>

            <div className="strip-stack">
              <section className="strip-card">
                <div>
                  <h3>{TEXT.nasdaqTitle}</h3>
                  <div className="metric-row">
                    <span>{TEXT.nasdaqDate} {latestNasdaq?.date ?? "-"}</span>
                    <strong>{latestNasdaq?.close?.toFixed(2) ?? "-"}</strong>
                  </div>
                </div>
                <div className="strip-meta">
                  <span>{TEXT.changeLabel} {latestNasdaq ? formatSigned(latestNasdaq.diff) : "-"}</span>
                  <span>{TEXT.rateLabel} {latestNasdaq ? formatSigned(latestNasdaq.rate) : "-"}%</span>
                </div>
                <span className="status-badge">Skill: Nasdaq</span>
              </section>

              <section className="strip-card">
                <div>
                  <h3>{TEXT.kospiTitle}</h3>
                  <div className="metric-row">
                    <span>{kospi?.market_state ?? "-"}</span>
                    <strong>{kospi?.index_value ?? "-"}</strong>
                  </div>
                </div>
                <div className="strip-meta">
                  <span>{TEXT.changeLabel} {kospi?.change_value ?? "-"}</span>
                  <span>{TEXT.rateLabel} {kospi?.change_percent ?? "-"}%</span>
                </div>
                <span className="status-badge">Skill: KOSPI</span>
              </section>
            </div>
          </div>

          <div className="market-chart-grid">
            <ChartPanel
              title={TEXT.nasdaqChart}
              color="#1f5f8b"
              data={nasdaqHistory
                .slice()
                .reverse()
                .map((item) => ({ label: item.date.slice(5), value: item.close }))}
            />
            <ChartPanel
              title={TEXT.kospiChart}
              color="#285f4b"
              data={kospiHistory
                .slice()
                .reverse()
                .map((item) => ({ label: item.date.slice(5), value: item.close }))}
            />
          </div>
        </article>

        <aside className="summary-panel">
          <span className="section-label">3-Line Summary</span>
          <div className="headline compact">
            <div>
              <h2>{TEXT.summaryTitle}</h2>
              <p>{TEXT.summaryBody}</p>
            </div>
          </div>

          <section className="score-box">
            <span>{TEXT.riskTitle}</span>
            <strong>{marketSummary.status_label}</strong>
            <small>{marketSummary.analysis_note}</small>
          </section>

          <div className="summary-lines">
            {marketSummary.summary_lines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">{marketSummary.source === "gpt" ? TEXT.sourceGpt : TEXT.sourceFallback}</div>
          <div className="layout-note">{TEXT.note}</div>
        </aside>
      </section>

      <section className="feed-panel">
        <span className="section-label">Live Community Feed</span>
        <div className="headline">
          <div>
            <h2>{TEXT.feedTitle}</h2>
            <p>{TEXT.feedBody}</p>
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

      <HourlyComparisonPanel data={data.hourlyComparison.points} />

      <section className="lower-grid">
        <ChartPanel
          title={TEXT.sentimentChart}
          data={data.sentiment.map((item) => ({
            label: item.snapshot_date.slice(5),
            value: item.sentiment_score,
          }))}
        />

        <ChartPanel
          title={TEXT.keywordChart}
          color="#285f4b"
          data={data.keywordTrends.map((item) => ({ label: item.keyword, value: item.mentions }))}
        />
      </section>
    </main>
  );
}
