import { FilterBar } from "@/components/filter-bar";
import { fetchNews } from "@/lib/api";

export default async function NewsPage() {
  const data = await fetchNews();

  return (
    <main className="stack" style={{ marginTop: 22 }}>
      <FilterBar title="News Monitor" description="Recent news documents stored in the platform database." />
      <section className="panel">
        <h2 className="panel-title">Latest News Headlines</h2>
        <div className="list">
          {data.items.map((item) => (
            <a className="list-item" href={item.canonical_url} key={item.id} target="_blank" rel="noreferrer">
              <div className="list-meta">
                {item.publisher ?? "unknown"} / {new Date(item.published_at).toLocaleString("ko-KR")}
              </div>
              <strong>{item.title}</strong>
              <p>{item.body}</p>
              <div className="tag-row">
                {item.tags.map((tag) => (
                  <span className="tag" key={`${item.id}-${tag}`}>
                    {tag}
                  </span>
                ))}
              </div>
            </a>
          ))}
          {data.items.length === 0 ? <div className="list-item">No news has been stored yet.</div> : null}
        </div>
      </section>
    </main>
  );
}
