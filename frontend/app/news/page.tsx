import { FilterBar } from "@/components/filter-bar";
import { getNews } from "@/lib/api";


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


export default async function NewsPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const query = toQuery(params);
  const data = await getNews(query);

  return (
    <main className="subpage-shell">
      <section className="subpage-hero">
        <span className="section-label">News Explorer</span>
        <h1>경제 뉴스 검색</h1>
        <p>날짜, 소스, 주제, 감정 기준으로 수집된 뉴스 데이터를 탐색할 수 있습니다.</p>
      </section>

      <div className="panel strong" style={{ marginBottom: 18 }}>
        <FilterBar
          action="/news"
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
              <p className="list-item-meta">{item.summary ?? "요약 없음"}</p>
            </a>
          ))}
        </div>
      </section>
    </main>
  );
}
