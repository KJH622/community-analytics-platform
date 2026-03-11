import { InlineBarPlot, InlineLinePlot, InlinePiePlot } from "@/components/charts";
import { TabsNav } from "@/components/tabs-nav";
import {
  CommunityPost,
  DailySnapshot,
  PoliticalDashboard,
  PoliticalPolarizationPoint,
  PoliticalSentiment,
  getKoreanMarketCommunityPosts,
  getMarketDashboardData,
  getPoliticsDashboardData,
  getPoliticsPolarization,
  getPoliticsSentiment,
} from "@/lib/api";


type PageProps = {
  searchParams: Promise<{ tab?: string }>;
};

type HotPostRow = {
  title: string;
  boardName: string;
  url: string;
  publishedAt: string | null;
  views: number;
  upvotes: number;
  comments: number;
  influence: number;
  status: string;
};

type TrendPoint = {
  label: string;
  value: number;
  secondary?: number;
};

export default async function HomePage({ searchParams }: PageProps) {
  const params = await searchParams;
  const activeTab = params.tab === "politics" ? "politics" : "market";

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand">
          <strong>마켓 시그널 허브</strong>
          <span>한국 경제·정치 커뮤니티 공개글 기반 여론 대시보드</span>
        </div>
        <div className="topbar-side">
          <nav>공지·정보성 글은 지수와 인기글 집계에서 제외</nav>
          <TabsNav activeTab={activeTab} />
        </div>
      </header>

      {activeTab === "market" ? <MarketTab /> : <PoliticsTab />}
    </main>
  );
}


async function MarketTab() {
  const [dashboard, communityResponse] = await Promise.all([
    getMarketDashboardData(),
    getKoreanMarketCommunityPosts(24),
  ]);

  const snapshots = dashboard.snapshots.slice(0, 3).slice().reverse();
  const latestSnapshot = snapshots[snapshots.length - 1] ?? dashboard.snapshots[0] ?? null;
  const hotPosts = buildHotPostRows(communityResponse.items).slice(0, 10);
  const keywordTrend = buildKeywordTrend(communityResponse.items, latestSnapshot);
  const topicShare =
    dashboard.topics.length > 0
      ? dashboard.topics
          .slice(0, 6)
          .map((item) => ({ name: topicNameMap[item.topic] ?? item.topic, value: item.count }))
      : buildFallbackTopics(latestSnapshot);
  const summaryLines = buildMarketSummaryLines(latestSnapshot, hotPosts, keywordTrend, snapshots);

  return (
    <>
      <section className="hero-grid">
        <article className="panel hero-panel">
          <span className="section-label">Korean Market Community Feed</span>
          <div className="headline-row">
            <div>
              <h1>최근 3일 경제 여론 흐름</h1>
              <p>
                디시인사이드 미국 주식·나스닥 갤러리의 공개 게시글 중 공지글, 운영글, 정보 정리글을
                제외하고 실제 의견이 드러나는 글만 골라 집계합니다.
              </p>
            </div>
            <p className="headline-note">오늘·어제·그제 기준 감정 경향성</p>
          </div>

          <div className="hero-chart-grid">
            <section className="chart-card chart-main">
              <div>
                <h3>커뮤니티 감정 추이</h3>
                <div className="metric">
                  <span>종합 감정 지수</span>
                  <strong>{formatScore(latestSnapshot?.sentiment_avg)}</strong>
                </div>
              </div>
              <InlineLinePlot
                data={buildMarketLinePoints(snapshots)}
                valueLabel="감정"
                secondaryLabel="공포/탐욕"
              />
              <div className="badge">
                공포/탐욕 {formatScore(latestSnapshot?.fear_greed_avg)} · 혐오 {formatScore(latestSnapshot?.hate_index_avg)}
              </div>
            </section>

            <div className="chart-stack">
              <section className="chart-card">
                <div>
                  <h3>감정 영향 키워드</h3>
                  <div className="metric">
                    <span>의견글 제목 기준 상위</span>
                    <strong>{keywordTrend[0]?.label ?? "-"}</strong>
                  </div>
                </div>
                <InlineBarPlot data={keywordTrend.slice(0, 6)} />
                <div className="badge">공지·정보성 글 제외 후 추출</div>
              </section>

              <section className="chart-card">
                <div>
                  <h3>대화 주제 비중</h3>
                  <div className="metric">
                    <span>최근 여론 중심 주제</span>
                    <strong>{topicShare[0]?.name ?? "-"}</strong>
                  </div>
                </div>
                <InlinePiePlot data={topicShare.slice(0, 5)} />
                <div className="badge">뉴스·커뮤니티 통합 토픽 비율</div>
              </section>
            </div>
          </div>
        </article>

        <aside className="panel summary-card">
          <span className="section-label">3-Line Summary</span>
          <div className="headline-row single">
            <div>
              <h2>경제 요약 3줄</h2>
              <p>사람들이 실제로 감정을 드러낸 글만 남겨서 분위기를 압축합니다.</p>
            </div>
          </div>

          <section className="score-box">
            <span>현재 시장 체감</span>
            <strong>{marketRegimeLabel(latestSnapshot)}</strong>
            <small>공지형·안내형 게시글을 제외한 의견글 기반 상태 카드입니다.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            현재 참고 소스: 디시인사이드 미국 주식 마이너 갤러리, 디시인사이드 나스닥 마이너 갤러리
          </div>
        </aside>
      </section>

      <section className="panel feed-card">
        <span className="section-label">Top 10 Sentiment Drivers</span>
        <div className="headline-row">
          <div>
            <h2>감정 지수에 가장 큰 영향을 준 글</h2>
            <p>최근 3일 의견글만 추려 반응량과 감정 강도를 함께 계산한 영향력 기준으로 정렬했습니다.</p>
          </div>
          <p className="headline-note">공지글·정보글·운영글은 제외</p>
        </div>

        <table aria-label="감정 영향 글 목록">
          <thead>
            <tr>
              <th className="rank">순위</th>
              <th>글 제목</th>
              <th>게시판</th>
              <th>반응</th>
              <th>영향력</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {hotPosts.map((post, index) => (
              <tr key={`${post.title}-${index}`}>
                <td className="rank">{String(index + 1).padStart(2, "0")}</td>
                <td className="title-cell">
                  <a href={post.url} target="_blank" rel="noreferrer">
                    <strong>{post.title}</strong>
                    {post.publishedAt ? `${formatDate(post.publishedAt)} 작성` : "최근 수집 글"}
                  </a>
                </td>
                <td>{post.boardName}</td>
                <td>
                  조회 {formatCompact(post.views)} / 추천 {formatCompact(post.upvotes)} / 댓글 {formatCompact(post.comments)}
                </td>
                <td>{post.influence}</td>
                <td>
                  <span className="badge">{post.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}


async function PoliticsTab() {
  const [dashboard, sentimentRows, polarizationRows] = await Promise.all([
    getPoliticsDashboardData(),
    getPoliticsSentiment(),
    getPoliticsPolarization(),
  ]);

  const snapshot = dashboard.sentiment_snapshot;
  const approvalIndicator = dashboard.indicators.find(
    (indicator) => indicator.code === "KR_PRESIDENT_APPROVAL"
  );
  const latestApprovalValue =
    approvalIndicator?.values && approvalIndicator.values.length > 0
      ? approvalIndicator.values[approvalIndicator.values.length - 1]?.value ?? null
      : null;
  const approvalTrend =
    approvalIndicator?.values && approvalIndicator.values.length > 0
      ? approvalIndicator.values.slice(-3).map((item) => ({
          label: shortDate(item.date),
          value: item.value,
        }))
      : buildPoliticalLinePoints(polarizationRows);
  const topPoliticians = dashboard.top_politicians
    .slice(0, 6)
    .map((item) => ({ label: item.keyword, value: item.count }));
  const keywordTrend = dashboard.keyword_trends
    .slice(0, 6)
    .map((item) => ({ label: item.keyword, value: item.count }));
  const hotPosts = buildHotPostRows(
    dashboard.posts.map((post) => ({
      id: post.id,
      title: post.title,
      board_name: post.board_name,
      body: null,
      published_at: post.published_at,
      view_count: post.view_count,
      upvotes: post.upvotes,
      comment_count: post.comment_count,
      url: post.url,
      influence_score: post.influence_score,
    }))
  ).slice(0, 10);
  const summaryLines = buildPoliticsSummaryLines(snapshot, dashboard, sentimentRows, polarizationRows);

  return (
    <>
      <section className="hero-grid">
        <article className="panel hero-panel">
          <span className="section-label">Korean Political Community Feed</span>
          <div className="headline-row">
            <div>
              <h1>최근 3일 정치 여론 흐름</h1>
              <p>
                공지성 글, 모집글, 입문 정리글을 제외하고 실제 정치 감정이 담긴 글만 골라 양극화와
                선거 관심도를 집계합니다.
              </p>
            </div>
            <p className="headline-note">최근 3일 정치 감정 추세</p>
          </div>

          <div className="hero-chart-grid">
            <section className="chart-card chart-main">
              <div>
                <h3>{approvalIndicator ? "대통령 지지율 추이" : "정치 감정 추이"}</h3>
                <div className="metric">
                  <span>{approvalIndicator ? "최근 지지율" : "정치 감정 지수"}</span>
                  <strong>
                    {latestApprovalValue !== null
                      ? latestApprovalValue.toFixed(1)
                      : formatScore(snapshot?.political_sentiment_avg)}
                  </strong>
                </div>
              </div>
              <InlineLinePlot
                data={approvalTrend}
                valueLabel={approvalIndicator ? "지지율" : "정치 감정"}
                secondaryLabel={!approvalIndicator ? "선거 관심도" : undefined}
              />
              <div className="badge">
                양극화 {formatScore(snapshot?.political_polarization_index)} · 선거 관심도 {formatScore(snapshot?.election_heat_index)}
              </div>
            </section>

            <div className="chart-stack">
              <section className="chart-card">
                <div>
                  <h3>정치인 언급 TOP</h3>
                  <div className="metric">
                    <span>최근 3일 최다 언급</span>
                    <strong>{topPoliticians[0]?.label ?? "-"}</strong>
                  </div>
                </div>
                <InlineBarPlot data={topPoliticians} />
                <div className="badge">공지성 글 제외 후 집계</div>
              </section>

              <section className="chart-card">
                <div>
                  <h3>정치 키워드 트렌드</h3>
                  <div className="metric">
                    <span>핵심 이슈</span>
                    <strong>{keywordTrend[0]?.label ?? "-"}</strong>
                  </div>
                </div>
                <InlineBarPlot data={keywordTrend} />
                <div className="badge">감정 기여도가 높은 글 기준</div>
              </section>
            </div>
          </div>
        </article>

        <aside className="panel summary-card">
          <span className="section-label">3-Line Summary</span>
          <div className="headline-row single">
            <div>
              <h2>정치 요약 3줄</h2>
              <p>운영성 글을 제거한 뒤 남은 정치 감정 신호만 정리합니다.</p>
            </div>
          </div>

          <section className="score-box">
            <span>현재 정치 체감</span>
            <strong>{politicsRegimeLabel(snapshot)}</strong>
            <small>정치 감정, 양극화, 선거 관심도를 최근 3일 기준으로 묶었습니다.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            현재 참고 소스: 디시인사이드 이재명 마이너 갤러리, 디시인사이드 보수주의 마이너 갤러리
          </div>
        </aside>
      </section>

      <section className="panel feed-card">
        <span className="section-label">Top 10 Sentiment Drivers</span>
        <div className="headline-row">
          <div>
            <h2>정치 감정에 가장 큰 영향을 준 글</h2>
            <p>최근 3일 정치 글 중 감정 강도와 반응량을 같이 반영한 영향력 기준으로 보여줍니다.</p>
          </div>
          <p className="headline-note">모집·공지·가이드성 글 제외</p>
        </div>

        <table aria-label="정치 감정 영향 글 목록">
          <thead>
            <tr>
              <th className="rank">순위</th>
              <th>글 제목</th>
              <th>게시판</th>
              <th>반응</th>
              <th>영향력</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {hotPosts.map((post, index) => (
              <tr key={`${post.title}-${index}`}>
                <td className="rank">{String(index + 1).padStart(2, "0")}</td>
                <td className="title-cell">
                  <a href={post.url} target="_blank" rel="noreferrer">
                    <strong>{post.title}</strong>
                    {post.publishedAt ? `${formatDate(post.publishedAt)} 작성` : "최근 수집 글"}
                  </a>
                </td>
                <td>{post.boardName}</td>
                <td>
                  조회 {formatCompact(post.views)} / 추천 {formatCompact(post.upvotes)} / 댓글 {formatCompact(post.comments)}
                </td>
                <td>{post.influence}</td>
                <td>
                  <span className="badge">{post.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel reference-panel">
        <span className="section-label">참고 커뮤니티</span>
        <div className="reference-grid">
          {dashboard.community_references.map((item) => (
            <div className="reference-card" key={item.name}>
              <div className="reference-top">
                <strong>{item.name}</strong>
                <span className="reference-leaning">{item.leaning ?? "미분류"}</span>
              </div>
              <p>{item.description ?? "설명 없음"}</p>
              {item.link ? (
                <a href={item.link} target="_blank" rel="noreferrer">
                  {item.link}
                </a>
              ) : null}
            </div>
          ))}
        </div>
      </section>
    </>
  );
}


function buildMarketLinePoints(snapshots: DailySnapshot[]): TrendPoint[] {
  const rows = snapshots.map((item) => ({
    label: shortDate(item.snapshot_date),
    value: item.sentiment_avg,
    secondary: item.fear_greed_avg,
  }));
  return rows.length > 0 ? rows : [{ label: "집계대기", value: 0, secondary: 0 }];
}


function buildPoliticalLinePoints(rows: PoliticalPolarizationPoint[]): TrendPoint[] {
  const items = rows.slice(-3).map((item) => ({
    label: shortDate(item.date),
    value: item.value,
    secondary: item.election_heat ?? undefined,
  }));
  return items.length > 0 ? items : [{ label: "집계대기", value: 0, secondary: 0 }];
}


function buildHotPostRows(posts: CommunityPost[]): HotPostRow[] {
  return posts
    .filter((post) => !post.analytics_excluded)
    .map((post) => {
      const views = post.view_count ?? 0;
      const upvotes = post.upvotes ?? 0;
      const comments = post.comment_count ?? 0;
      const influence = Math.round(post.influence_score ?? 0);

      return {
        title: post.title,
        boardName: post.board_name,
        url: post.url,
        publishedAt: post.published_at,
        views,
        upvotes,
        comments,
        influence,
        status: influence >= 170 ? "경고" : influence >= 120 ? "주의" : "관망",
      };
    })
    .sort((left, right) => right.influence - left.influence || right.views - left.views);
}


function buildKeywordTrend(posts: CommunityPost[], snapshot: DailySnapshot | null) {
  const stopwords = new Set([
    "오늘",
    "진짜",
    "근데",
    "지금",
    "무슨",
    "그냥",
    "이거",
    "저거",
    "정도",
    "미국",
    "주식",
    "나스닥",
    "갤러리",
  ]);
  const counts = new Map<string, number>();

  for (const post of posts) {
    if (post.analytics_excluded) {
      continue;
    }
    const tokens = post.title.match(/[A-Za-z0-9가-힣]{2,}/g) ?? [];
    for (const token of tokens) {
      const normalized = token.toLowerCase();
      if (stopwords.has(normalized)) {
        continue;
      }
      counts.set(normalized, (counts.get(normalized) ?? 0) + 1);
    }
  }

  const ranked = [...counts.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, 8)
    .map(([label, value]) => ({ label, value }));

  if (ranked.length > 0) {
    return ranked;
  }
  return (snapshot?.top_keywords ?? ["대기"]).slice(0, 6).map((keyword, index) => ({
    label: keyword,
    value: 6 - index,
  }));
}


function buildFallbackTopics(snapshot: DailySnapshot | null) {
  return (snapshot?.top_keywords ?? ["경제", "환율", "금리"]).slice(0, 5).map((keyword, index) => ({
    name: keyword,
    value: 5 - index,
  }));
}


function buildMarketSummaryLines(
  snapshot: DailySnapshot | null,
  hotPosts: HotPostRow[],
  keywordTrend: Array<{ label: string; value: number }>,
  trendRows: DailySnapshot[]
) {
  const hottest = hotPosts[0];
  const topKeywords = keywordTrend.slice(0, 3).map((item) => item.label).join(", ") || "집계 대기";
  const trendText =
    trendRows.length >= 3
      ? `${trendRows[0].snapshot_date}, ${trendRows[1].snapshot_date}, ${trendRows[2].snapshot_date}`
      : "최근 3일";

  return [
    hottest
      ? `감정 영향력이 가장 큰 글은 ${hottest.boardName}의 '${truncate(hottest.title, 30)}'이며 영향력 점수는 ${hottest.influence}입니다.`
      : "최근 3일 기준으로 집계된 의견글이 아직 없습니다.",
    `최근 의견글에서 반복된 핵심 키워드는 ${topKeywords} 순입니다.`,
    snapshot
      ? `${trendText} 기준 공포/탐욕 ${formatScore(snapshot.fear_greed_avg)}, 혐오 ${formatScore(snapshot.hate_index_avg)}, 불확실성 ${formatScore(snapshot.uncertainty_avg)}로 집계되었습니다.`
      : "최근 3일 감정 스냅샷이 아직 준비되지 않았습니다.",
  ];
}


function buildPoliticsSummaryLines(
  snapshot: PoliticalDashboard["sentiment_snapshot"],
  dashboard: PoliticalDashboard,
  sentimentRows: PoliticalSentiment[],
  polarizationRows: PoliticalPolarizationPoint[]
) {
  const topPolitician = dashboard.top_politicians[0]?.keyword ?? "집계 대기";
  const topKeyword = dashboard.keyword_trends[0]?.keyword ?? "집계 대기";
  const averages = sentimentRows.length
    ? {
        support: average(sentimentRows.map((item) => item.support_score)),
        opposition: average(sentimentRows.map((item) => item.opposition_score)),
        anger: average(sentimentRows.map((item) => item.anger_score)),
      }
    : null;
  const trendText =
    polarizationRows.length >= 3
      ? `${polarizationRows[0].date}, ${polarizationRows[1].date}, ${polarizationRows[2].date}`
      : "최근 3일";

  return [
    `최근 3일 최다 언급 정치인은 ${topPolitician}이고, 핵심 키워드는 ${topKeyword}입니다.`,
    averages
      ? `정치 감정 평균은 지지 ${formatScore(averages.support)}, 반대 ${formatScore(averages.opposition)}, 분노 ${formatScore(averages.anger)}입니다.`
      : "정치 감정 세부 평균은 아직 집계 대기 상태입니다.",
    snapshot
      ? `${trendText} 기준 양극화 ${formatScore(snapshot.political_polarization_index)}, 선거 관심도 ${formatScore(snapshot.election_heat_index)}, 정치 감정 ${formatScore(snapshot.political_sentiment_avg)}로 정리됩니다.`
      : "정치 일별 스냅샷이 아직 준비되지 않았습니다.",
  ];
}


function marketRegimeLabel(snapshot: DailySnapshot | null) {
  if (!snapshot) {
    return "집계중";
  }
  if (snapshot.hate_index_avg >= 45 || snapshot.fear_greed_avg >= 68) {
    return "과열";
  }
  if (snapshot.fear_greed_avg <= 35 || snapshot.uncertainty_avg >= 55) {
    return "경계";
  }
  return "관망";
}


function politicsRegimeLabel(snapshot: PoliticalDashboard["sentiment_snapshot"]) {
  if (!snapshot) {
    return "집계중";
  }
  if (snapshot.political_polarization_index >= 65) {
    return "격화";
  }
  if (snapshot.election_heat_index >= 55) {
    return "집중";
  }
  return "안정";
}


function average(values: number[]) {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}


function formatScore(value: number | null | undefined) {
  return value === null || value === undefined ? "-" : value.toFixed(1);
}


function formatCompact(value: number) {
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}


function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}


function shortDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "numeric",
    day: "numeric",
  }).format(new Date(value));
}


function truncate(value: string, maxLength: number) {
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}…`;
}


const topicNameMap: Record<string, string> = {
  rates: "금리",
  inflation: "물가",
  fx: "환율",
  semiconductors: "반도체",
  ai: "AI",
};
