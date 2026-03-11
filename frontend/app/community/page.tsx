import { FilterBar } from "@/components/filter-bar";
import { getCommunityPosts } from "@/lib/api";


type PageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};


function toQuery(params: Record<string, string | string[] | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === "string" && value) {
      search.set(key, value);
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}


export default async function CommunityPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const query = toQuery(params);
  const data = await getCommunityPosts(query);

  return (
    <main className="subpage-shell">
      <section className="subpage-hero">
        <span className="section-label">Community Explorer</span>
        <h1>커뮤니티 글 검색</h1>
        <p>경제·정치 커뮤니티에서 수집한 공개 글을 날짜, 소스, 주제, 감정 기준으로 조회합니다.</p>
      </section>

      <div className="panel strong" style={{ marginBottom: 18 }}>
        <FilterBar
          action="/community"
          defaults={{
            date_from: typeof params.date_from === "string" ? params.date_from : undefined,
            source: typeof params.source === "string" ? params.source : undefined,
            country: typeof params.country === "string" ? params.country : undefined,
            topic: typeof params.topic === "string" ? params.topic : undefined,
            sentiment: typeof params.sentiment === "string" ? params.sentiment : undefined,
          }}
        />
      </div>

      <section className="panel">
        <h3>검색 결과 {data.total}건</h3>
        <div className="list">
          {data.items.map((item) => (
            <a href={item.url} key={item.id} className="list-item" target="_blank" rel="noreferrer">
              <p className="list-item-title">{item.title}</p>
              <p className="list-item-meta">
                {item.board_name} · 추천 {item.upvotes ?? 0} · 댓글 {item.comment_count ?? 0}
              </p>
            </a>
          ))}
        </div>
      </section>
    </main>
  );
}
