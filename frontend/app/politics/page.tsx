import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { MetricCard } from "@/components/metric-card";
import { fetchCommunity, fetchDashboardData } from "@/lib/api";

export default async function PoliticsPage() {
  const [dashboard, politicsPosts] = await Promise.all([
    fetchDashboardData(),
    fetchCommunity({ topicCategory: "politics", pageSize: 12 }),
  ]);

  const latest = dashboard.sentiment[0] ?? null;
  const topKeyword = dashboard.keywordTrends[0]?.keyword ?? "No keyword";

  return (
    <main>
      <DomainTabs active="politics" />
      <div className="page-grid">
        <section className="stack">
          <div className="panel">
            <h2 className="panel-title">Politics Snapshot</h2>
            <div className="card-grid">
              <MetricCard
                label="Political Sentiment"
                value={(latest?.sentiment_score ?? 0).toFixed(1)}
                caption="Latest daily sentiment snapshot"
              />
              <MetricCard
                label="Hate Index"
                value={(latest?.hate_index ?? 0).toFixed(1)}
                caption="Useful for hostility and tension tracking"
              />
              <MetricCard
                label="Uncertainty"
                value={(latest?.uncertainty_score ?? 0).toFixed(1)}
                caption="Useful for ambiguity and rumor-sensitive days"
              />
              <MetricCard
                label="Top Keyword"
                value={topKeyword}
                caption="Most mentioned term in the latest keyword trend list"
              />
            </div>
          </div>

          <ChartPanel
            title="Sentiment Trend"
            data={dashboard.sentiment.map((item) => ({ label: item.snapshot_date.slice(5), value: item.sentiment_score }))}
          />

          <ChartPanel
            title="Hate Trend"
            color="#285f4b"
            data={dashboard.sentiment.map((item) => ({ label: item.snapshot_date.slice(5), value: item.hate_index }))}
          />

          <ChartPanel
            title="Keyword Trend"
            color="#872341"
            data={dashboard.keywordTrends.map((item) => ({ label: item.keyword, value: item.mentions }))}
          />

          <div className="layout-note">
            This page uses the same crawler database as the market dashboard, but filtered for politics-oriented analysis.
          </div>
        </section>

        <aside className="stack">
          <div className="panel">
            <h2 className="panel-title">Latest Political Community Posts</h2>
            <LiveCommunityFeed initialPosts={politicsPosts.items} topicCategory="politics" limit={12} variant="list" />
          </div>
        </aside>
      </div>
    </main>
  );
}
