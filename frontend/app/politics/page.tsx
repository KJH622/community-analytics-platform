import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { MetricCard } from "@/components/metric-card";
import { TopicDonut } from "@/components/topic-donut";
import { fetchPoliticsDashboard } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PoliticsPage() {
  const data = await fetchPoliticsDashboard();
  const approval = data.indicator_cards.find((item) => item.code === "president_approval");
  const national = data.indicator_cards.find((item) => item.code === "national_performance");
  const partyLatest = data.indicator_cards.find((item) => item.code === "party_support");
  const latestSentiment = data.political_sentiment_index.at(-1)?.value ?? 0;
  const latestPolarization = data.polarization_index.at(-1)?.value ?? 0;
  const latestElectionHeat = data.election_heat_index.at(-1)?.value ?? 0;

  return (
    <main>
      <DomainTabs active="politics" />
      <div className="page-grid">
        <section className="stack">
          <div className="panel">
            <h2 className="panel-title">Political Indicator Cards</h2>
            <div className="card-grid">
              <MetricCard label="President Approval" value={`${approval?.value ?? 0}%`} caption={approval?.source ?? "sample"} />
              <MetricCard label="Party Support" value={`${partyLatest?.value ?? 0}%`} caption={partyLatest?.label ?? "sample"} />
              <MetricCard label="Political Sentiment" value={`${latestSentiment}`} caption="Community sentiment composite" />
              <MetricCard label="Polarization Index" value={`${latestPolarization}`} caption="Support, opposition, anger spread" />
              <MetricCard label="Election Heat" value={`${latestElectionHeat}`} caption="Election-related mention intensity" />
              <MetricCard label="National Performance" value={`${national?.value ?? 0}%`} caption={national?.label ?? "positive"} />
            </div>
          </div>

          <ChartPanel
            title="President Approval Trend"
            data={data.approval_trend.map((item) => ({ label: item.date.slice(5), value: item.value }))}
          />

          <ChartPanel
            title="Political Keyword Trend"
            color="#285f4b"
            data={data.keyword_trends.map((item) => ({ label: item.keyword, value: item.mentions }))}
          />

          <ChartPanel
            title="Political Sentiment Index"
            color="#872341"
            data={data.political_sentiment_index.map((item) => ({ label: item.date.slice(5), value: item.value }))}
          />

          <div className="panel">
            <h2 className="panel-title">Political Community Posts</h2>
            <div className="list">
              {data.community_posts.map((item) => (
                <a className="list-item" href={item.original_url} key={item.id} target="_blank">
                  <div className="list-meta">
                    {item.board_name ?? item.community_name} - Views {item.view_count ?? 0}
                  </div>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                </a>
              ))}
            </div>
          </div>
        </section>

        <aside className="stack">
          <TopicDonut
            title="Politician Mentions Top 10"
            data={data.politician_mentions_top10.map((item) => ({ topic: item.name, documents: item.mentions }))}
          />
          <ChartPanel
            title="Political Polarization Index"
            color="#1f5f8b"
            data={data.polarization_index.map((item) => ({ label: item.date.slice(5), value: item.value }))}
          />
          <ChartPanel
            title="Election Interest Index"
            color="#b5532f"
            data={data.election_heat_index.map((item) => ({ label: item.date.slice(5), value: item.value }))}
          />
          <div className="panel">
            <h2 className="panel-title">Reference Communities</h2>
            <div className="list">
              {data.reference_communities.map((item) => (
                <a className="list-item" href={item.link} key={item.name} target="_blank">
                  <div className="list-meta">
                    {item.leaning ?? "unknown"} - {item.status}
                  </div>
                  <strong>{item.name}</strong>
                  <p>{item.description}</p>
                </a>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
