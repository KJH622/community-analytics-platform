import { ChartPanel } from "@/components/chart-panel";
import { FilterBar } from "@/components/filter-bar";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { fetchCommunity, fetchDashboardData } from "@/lib/api";

export default async function CommunityPage() {
  const [community, dashboard] = await Promise.all([
    fetchCommunity({ boardName: "stockus-concept", pageSize: 20 }),
    fetchDashboardData(),
  ]);

  return (
    <main className="stack" style={{ marginTop: 22 }}>
      <FilterBar title="Community Feed" />
      <div className="page-grid">
        <section className="panel">
          <h2 className="panel-title">Live StockUS Concept Posts with Hate Analysis</h2>
          <LiveCommunityFeed
            initialPosts={community.items}
            boardId="stockus"
            boardName="stockus-concept"
            limit={20}
            variant="list"
          />
        </section>

        <section className="stack">
          <ChartPanel
            title="Hate Index"
            color="#872341"
            data={dashboard.sentiment.map((item) => ({
              label: item.snapshot_date.slice(5),
              value: item.hate_index,
            }))}
          />
          <ChartPanel
            title="Fear / Greed"
            color="#1f5f8b"
            data={dashboard.sentiment.map((item) => ({
              label: item.snapshot_date.slice(5),
              value: item.fear_greed_score,
            }))}
          />
        </section>
      </div>
    </main>
  );
}
