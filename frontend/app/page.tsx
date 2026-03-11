import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { MetricCard } from "@/components/metric-card";
import { fetchCommunity, fetchDashboardData } from "@/lib/api";

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value == null) {
    return "-";
  }
  return value.toFixed(digits);
}

export default async function DashboardPage() {
  const [data, community] = await Promise.all([
    fetchDashboardData(),
    fetchCommunity({ topicCategory: "economy", pageSize: 8 }),
  ]);

  const latest = data.sentiment[0] ?? null;
  const latestIndicator = data.indicators.find((item) => item.latest_release) ?? null;
  const topKeywords = latest?.top_keywords?.slice(0, 4).join(", ") || "No daily keywords yet";
  const summaryLines = [
    `Current daily sentiment is ${formatNumber(latest?.sentiment_score)}.`,
    `Hate index is ${formatNumber(latest?.hate_index)} and uncertainty is ${formatNumber(latest?.uncertainty_score)}.`,
    `Top keywords today: ${topKeywords}.`,
  ];

  return (
    <main className="dashboard-page">
      <DomainTabs active="market" />

      <section className="hero-grid">
        <article className="feature-panel">
          <span className="section-label">Market Snapshot</span>
          <div className="headline">
            <div>
              <h1>Community-driven market view</h1>
              <p>Economic community posts, analytics snapshots, and headline data in one place.</p>
            </div>
            <p>Updated from the crawler pipeline every hour.</p>
          </div>

          <div className="card-grid">
            <MetricCard
              label="Daily Sentiment"
              value={formatNumber(latest?.sentiment_score)}
              caption="Average score from the latest daily snapshot"
            />
            <MetricCard
              label="Fear / Greed"
              value={formatNumber(latest?.fear_greed_score)}
              caption="Market emotion balance across stored posts"
            />
            <MetricCard
              label="Hate Index"
              value={formatNumber(latest?.hate_index)}
              caption="Aggression and hostility detected in the feed"
            />
            <MetricCard
              label="Latest Indicator"
              value={latestIndicator?.latest_release?.actual_value?.toString() ?? "-"}
              caption={latestIndicator ? `${latestIndicator.name} (${latestIndicator.country})` : "No indicator release yet"}
            />
          </div>
        </article>

        <aside className="summary-panel">
          <span className="section-label">3-Line Summary</span>
          <div className="headline compact">
            <div>
              <h2>Today at a glance</h2>
              <p>A fast read on how the community feed is moving right now.</p>
            </div>
          </div>

          <section className="score-box">
            <span>Alert level</span>
            <strong>{(latest?.hate_index ?? 0) >= 40 ? "HIGH" : "WATCH"}</strong>
            <small>Use this as a quick proxy before deeper sentiment analysis runs.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            This dashboard is reading from the crawler database, not scraping the community live on every page request.
          </div>
        </aside>
      </section>

      <section className="feed-panel">
        <span className="section-label">Economy Feed</span>
        <div className="headline">
          <div>
            <h2>Latest economy community posts</h2>
            <p>Posts are already stored in the database and refreshed on a one-minute UI polling loop.</p>
          </div>
          <p>{community.total} stored economy posts</p>
        </div>

        <LiveCommunityFeed initialPosts={community.items} topicCategory="economy" limit={8} variant="table" />
      </section>

      <section className="lower-grid">
        <ChartPanel
          title="Sentiment Trend"
          data={data.sentiment.map((item) => ({
            label: item.snapshot_date.slice(5),
            value: item.sentiment_score,
          }))}
        />

        <ChartPanel
          title="Keyword Trend"
          color="#285f4b"
          data={data.keywordTrends.map((item) => ({ label: item.keyword, value: item.mentions }))}
        />
      </section>
    </main>
  );
}
