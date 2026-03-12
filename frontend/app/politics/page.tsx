import { DomainTabs } from "@/components/domain-tabs";
import { MetricCard } from "@/components/metric-card";
import { PoliticsPolarizationChart } from "@/components/politics-polarization-chart";
import { fetchPoliticsDashboard } from "@/lib/api";

function formatDateLabel(value: string | null) {
  if (!value) {
    return "데이터 준비 중";
  }
  const date = new Date(value);
  return `${date.getMonth() + 1}월 ${date.getDate()}일 기준`;
}

function formatShortDate(value: string) {
  const date = new Date(value);
  return `${date.getMonth() + 1}.${date.getDate()}`;
}

function truncateText(value: string, length = 160) {
  if (value.length <= length) {
    return value;
  }
  return `${value.slice(0, length).trim()}...`;
}

function stanceLabel(value: string) {
  if (value === "support") {
    return "찬성";
  }
  if (value === "oppose") {
    return "반대";
  }
  return "중립";
}

function emotionLabel(value: string) {
  if (value === "anger") {
    return "분노";
  }
  if (value === "positive") {
    return "긍정";
  }
  return "중립";
}

export default async function PoliticsPage() {
  const data = await fetchPoliticsDashboard();

  return (
    <main className="dashboard-page">
      <DomainTabs active="politics" />

      <section className="hero-grid">
        <article className="feature-panel">
          <span className="section-label">Politics Dashboard</span>
          <div className="headline">
            <div>
              <h1>정치 커뮤니티 대시보드</h1>
              <p>크롤서버가 저장한 실제 정치 게시글만 기준으로 이슈, 반응, 정치인 언급량을 집계합니다.</p>
            </div>
            <p>{formatDateLabel(data.reference_date)}</p>
          </div>

          <div className="card-grid">
            <MetricCard label="정치 글 수" value={`${data.summary.post_count}`} caption="최근 30일 정치 게시글 수" />
            <MetricCard label="오늘 글 수" value={`${data.summary.today_post_count}`} caption="최근 기준일 정치 게시글 수" />
            <MetricCard label="가장 뜨거운 이슈" value={data.summary.top_issue ?? "-"} caption="최근 30일 최다 언급 이슈" />
            <MetricCard
              label="최다 언급 정치인"
              value={data.summary.top_politician ?? "-"}
              caption="최근 기준일 기준 최다 언급"
            />
          </div>
        </article>

        <aside className="summary-panel">
          <span className="section-label">오늘 정치 커뮤니티 감정</span>
          <div className="headline compact">
            <div>
              <h2>오늘의 감정 분포</h2>
              <p>분노, 긍정, 중립 비율을 오늘 기준 정치 게시글로 계산했습니다.</p>
            </div>
          </div>

          <div className="politics-emotion-grid">
            <div className="politics-emotion-card" data-tone="anger">
              <span>분노</span>
              <strong>{data.today_emotion.anger_pct.toFixed(1)}%</strong>
            </div>
            <div className="politics-emotion-card" data-tone="positive">
              <span>긍정</span>
              <strong>{data.today_emotion.positive_pct.toFixed(1)}%</strong>
            </div>
            <div className="politics-emotion-card" data-tone="neutral">
              <span>중립</span>
              <strong>{data.today_emotion.neutral_pct.toFixed(1)}%</strong>
            </div>
          </div>

          <section className="score-box">
            <span>샘플 수</span>
            <strong>{data.today_emotion.mentions}</strong>
            <small>정치 커뮤니티 감정 계산에 사용된 기준일 게시글 수입니다.</small>
          </section>
        </aside>
      </section>

      <section className="panel">
        <div className="headline">
          <div>
            <h2>양극 지지율 그래프</h2>
            <p>최근 14일 동안 정치 게시글의 찬성, 반대, 중립 비중을 날짜별로 비교합니다.</p>
          </div>
        </div>
        <PoliticsPolarizationChart data={data.polarization_trend} />
      </section>

      <section className="page-grid">
        <section className="stack">
          <div className="panel">
            <h2 className="panel-title">정치 감정 분석</h2>
            <div className="politics-bar-list">
              {data.issue_sentiments.map((issue) => (
                <article className="politics-bar-card" key={issue.issue}>
                  <div className="politics-bar-head">
                    <strong>{issue.issue}</strong>
                    <span>{issue.mentions}건</span>
                  </div>
                  <div className="politics-stacked-bar" aria-label={`${issue.issue} 감정 비율`}>
                    <span className="politics-bar-segment politics-bar-positive" style={{ width: `${issue.positive_pct}%` }} />
                    <span className="politics-bar-segment politics-bar-negative" style={{ width: `${issue.negative_pct}%` }} />
                    <span className="politics-bar-segment politics-bar-neutral" style={{ width: `${issue.neutral_pct}%` }} />
                  </div>
                  <div className="politics-bar-meta">
                    <span>긍정 {issue.positive_pct.toFixed(1)}%</span>
                    <span>부정 {issue.negative_pct.toFixed(1)}%</span>
                    <span>중립 {issue.neutral_pct.toFixed(1)}%</span>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <h2 className="panel-title">커뮤니티별 반응 비교</h2>
            <div className="stack">
              {data.issue_source_comparisons.map((issue) => (
                <article className="politics-issue-card" key={issue.issue}>
                  <div className="politics-bar-head">
                    <strong>{issue.issue}</strong>
                    <span>커뮤니티별 찬반 비율</span>
                  </div>
                  <div className="politics-source-list">
                    {issue.sources.map((source) => (
                      <div className="politics-source-row" key={`${issue.issue}-${source.source_code}`}>
                        <div className="politics-source-name">
                          <strong>{source.source_name}</strong>
                          <span>{source.mentions}건</span>
                        </div>
                        <div className="politics-stacked-bar">
                          <span className="politics-bar-segment politics-bar-positive" style={{ width: `${source.support_pct}%` }} />
                          <span className="politics-bar-segment politics-bar-negative" style={{ width: `${source.oppose_pct}%` }} />
                          <span className="politics-bar-segment politics-bar-neutral" style={{ width: `${source.neutral_pct}%` }} />
                        </div>
                        <div className="politics-source-meta">
                          <span>찬성 {source.support_pct.toFixed(1)}%</span>
                          <span>반대 {source.oppose_pct.toFixed(1)}%</span>
                          <span>중립 {source.neutral_pct.toFixed(1)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="headline compact">
              <div>
                <h2>핫글 모음</h2>
                <p>조회수, 반응 수, 감정 강도를 함께 반영해 상위 정치 글을 정렬했습니다.</p>
              </div>
            </div>

            <div className="politics-hot-list">
              {data.hot_posts.map((post) => (
                <a className="politics-hot-post" href={post.original_url} key={post.id} target="_blank" rel="noreferrer">
                  <div className="politics-hot-top">
                    <div className="politics-hot-meta">
                      <span>{post.source_name}</span>
                      <span>{post.board_name}</span>
                      <span>{formatShortDate(post.created_at)}</span>
                    </div>
                    <span className="status-badge">점수 {post.influence_score.toFixed(1)}</span>
                  </div>

                  <strong>{post.title}</strong>
                  <p>{truncateText(post.body)}</p>

                  <div className="politics-hot-tags">
                    {post.issue_labels.map((label) => (
                      <span className="keyword-chip" key={`${post.id}-${label}`}>
                        {label}
                      </span>
                    ))}
                    <span className="signal-badge">{stanceLabel(post.stance)}</span>
                    <span className="signal-badge">{emotionLabel(post.emotion)}</span>
                  </div>

                  <div className="politics-hot-meta">
                    <span>조회 {post.view_count ?? 0}</span>
                    <span>댓글 {post.comment_count ?? 0}</span>
                    <span>추천 {post.upvotes ?? 0}</span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </section>

        <aside className="stack">
          <div className="panel">
            <h2 className="panel-title">정치인 언급량 순위</h2>
            <ol className="politics-ranking-list">
              {data.politician_rankings.map((item) => (
                <li className="politics-ranking-item" key={item.name}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.mentions}건 언급</span>
                  </div>
                  <span className="status-badge">TOP</span>
                </li>
              ))}
            </ol>
          </div>

          <div className="panel">
            <h2 className="panel-title">이슈 타임라인</h2>
            <div className="politics-timeline">
              {data.issue_timeline.map((event) => (
                <article className="politics-timeline-item" key={`${event.date}-${event.headline}`}>
                  <span>{formatShortDate(event.date)}</span>
                  <strong>{event.issue}</strong>
                  <p>{event.headline}</p>
                </article>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
