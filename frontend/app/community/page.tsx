import { FilterBar } from "@/components/filter-bar";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { fetchCommunity } from "@/lib/api";

export default async function CommunityPage() {
  const [economyPosts, politicsPosts] = await Promise.all([
    fetchCommunity({ topicCategory: "economy", pageSize: 12 }),
    fetchCommunity({ topicCategory: "politics", pageSize: 12 }),
  ]);

  return (
    <main className="stack" style={{ marginTop: 22 }}>
      <FilterBar
        title="Community Feed"
        description="Stored posts from Ppomppu, Bobaedream, and allowed Clien boards."
      />
      <div className="page-grid">
        <section className="panel">
          <h2 className="panel-title">Economy Posts</h2>
          <LiveCommunityFeed initialPosts={economyPosts.items} topicCategory="economy" limit={12} variant="list" />
        </section>

        <section className="panel">
          <h2 className="panel-title">Politics Posts</h2>
          <LiveCommunityFeed initialPosts={politicsPosts.items} topicCategory="politics" limit={12} variant="list" />
        </section>
      </div>
    </main>
  );
}
