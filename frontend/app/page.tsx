import { InlineBarPlot, InlineLinePlot } from "@/components/charts";
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

type TrendPoint = {
  label: string;
  value: number;
  secondary?: number;
};

type RatioPoint = {
  label: string;
  value: number;
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
  reason: string;
};

export default async function HomePage({ searchParams }: PageProps) {
  const params = await searchParams;
  const activeTab = params.tab === "politics" ? "politics" : "market";

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand">
          <strong>마켓 시그널 허브</strong>
          <span>한국어 경제·정치 커뮤니티 공개 글 기반 여론 분석 대시보드</span>
        </div>
        <div className="topbar-side">
          <nav>최근 30일, 공지 제외, 감정이 실제로 드러난 글만 집계</nav>
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
    getKoreanMarketCommunityPosts(100),
  ]);

  const snapshots = dashboard.snapshots.slice().reverse();
  const latestSnapshot = snapshots[snapshots.length - 1] ?? null;
  const emotionalPosts = communityResponse.items.filter(
    (post) => !post.analytics_excluded && post.emotional_signal
  );
  const ratios = buildMarketRatios(emotionalPosts);
  const hotPosts = buildHotPostRows(emotionalPosts).slice(0, 10);
  const summaryLines = buildMarketSummary(latestSnapshot, emotionalPosts, hotPosts, ratios);

  return (
    <>
      <section className="hero-grid">
        <article className="panel hero-panel">
          <span className="section-label">Korean Market Community Feed</span>
          <div className="headline-row">
            <div>
              <h1>최근 30일 경제 커뮤니티 감정 흐름</h1>
              <p>
                이제는 일반 잡담보다 하루 최대 30개 수준의 반응 있는 글만 모으고, 감정이 거의 없는 글은
                집계에서 제외합니다. 목표는 공포와 환희가 실제로 어느 날 강하게 나타났는지 보는 것입니다.
              </p>
            </div>
            <p className="headline-note">최근 30일 감정 포함 의견글 {emotionalPosts.length}건</p>
          </div>

          <div className="hero-chart-grid">
            <section className="chart-card chart-main">
              <div>
                <h3>30일 감정 추이</h3>
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
                공포/탐욕 {formatScore(latestSnapshot?.fear_greed_avg)} / 혐오 {formatScore(latestSnapshot?.hate_index_avg)}
              </div>
            </section>

            <div className="chart-stack">
              <section className="chart-card">
                <div>
                  <h3>긍정 / 부정 / 관망 비율</h3>
                  <div className="metric">
                    <span>최근 30일 감정글 기준</span>
                    <strong>{ratios[0]?.value ?? 0}%</strong>
                  </div>
                </div>
                <InlineBarPlot data={ratios} />
                <div className="badge">
                  공지글과 감정 없는 글을 제외한 뒤 비율을 다시 계산합니다.
                </div>
              </section>

              <section className="chart-card">
                <div>
                  <h3>실험용 체크포인트</h3>
                  <div className="metric">
                    <span>공포에 사고 환희에 팔아라</span>
                    <strong>{marketExperimentLabel(latestSnapshot)}</strong>
                  </div>
                </div>
                <div className="mini-summary">
                  <p>공포 지수가 낮게 깔리고 부정 비율이 높으면 매수 후보 구간으로 보기 좋습니다.</p>
                  <p>탐욕 지수가 높고 긍정 비율이 과열되면 차익 실현 후보 구간으로 실험할 수 있습니다.</p>
                  <p>이제 30일 단위로 흐름을 모아 두어서 이후 백테스트 지표와 연결하기 쉬워졌습니다.</p>
                </div>
              </section>
            </div>
          </div>
        </article>

        <aside className="panel summary-card">
          <span className="section-label">오른쪽 요약</span>
          <div className="headline-row single">
            <div>
              <h2>오늘 읽힌 분위기와 이유</h2>
              <p>
                요약은 이제 오른쪽에 합쳐서 보여줍니다. 키워드 나열 대신 최근 30일 감정 비율, 상위 영향글,
                공포·탐욕·혐오 수치를 한 번에 읽을 수 있게 정리했습니다.
              </p>
            </div>
          </div>

          <section className="score-box">
            <span>현재 체감 상태</span>
            <strong>{marketRegimeLabel(latestSnapshot)}</strong>
            <small>감정이 실제로 드러난 글만 남긴 뒤 계산한 결과입니다.</small>
          </section>

          <div className="summary-lines">
            {summaryLines.map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            참고 소스: 뽐뿌 증권포럼 핫/인기
          </div>
        </aside>
      </section>

      <section className="panel feed-card">
        <span className="section-label">Top 10 Sentiment Drivers</span>
        <div className="headline-row">
          <div>
            <h2>감정 지수에 가장 큰 영향을 준 글</h2>
            <p>단순 인기순이 아니라 감정 강도와 반응량을 함께 반영한 영향도 기준입니다.</p>
          </div>
          <p className="headline-note">최근 30일, 공지 제외, 감정글만</p>
        </div>

        <table aria-label="경제 감정 영향 글 목록">
          <thead>
            <tr>
              <th className="rank">순위</th>
              <th>글 제목</th>
              <th>게시판</th>
              <th>반응</th>
              <th>영향도</th>
              <th>이유</th>
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
                <td>
                  <div>{post.influence}</div>
                  <span className="badge">{post.status}</span>
                </td>
                <td>{post.reason}</td>
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
  const ratios = buildPoliticsRatios(sentimentRows);
  const posts = dashboard.posts.filter((post) => !post.analytics_excluded);
  const topPostTitle = posts[0]?.title ?? "집계 대기";

  return (
    <>
      <section className="hero-grid">
        <article className="panel hero-panel">
          <span className="section-label">Korean Political Community Feed</span>
          <div className="headline-row">
            <div>
              <h1>최근 30일 정치 여론 흐름</h1>
              <p>
                정치 탭은 기존 구조를 유지하되, 오른쪽 요약에 핵심 해석을 몰아 넣었습니다. 추후 경제 탭과
                같은 방식으로 감정 없는 글 제외 기준을 더 강화할 수 있습니다.
              </p>
            </div>
            <p className="headline-note">현재 분석 대상 정치 글 {sentimentRows.length}건</p>
          </div>

          <div className="hero-chart-grid">
            <section className="chart-card chart-main">
              <div>
                <h3>정치 감정 추이</h3>
                <div className="metric">
                  <span>정치 감정 지수</span>
                  <strong>{formatScore(snapshot?.political_sentiment_avg)}</strong>
                </div>
              </div>
              <InlineLinePlot
                data={buildPoliticalLinePoints(polarizationRows)}
                valueLabel="양극화"
                secondaryLabel="선거 관심도"
              />
              <div className="badge">
                양극화 {formatScore(snapshot?.political_polarization_index)} / 선거 관심도 {formatScore(snapshot?.election_heat_index)}
              </div>
            </section>

            <div className="chart-stack">
              <section className="chart-card">
                <div>
                  <h3>지지 / 반대 / 유보 비율</h3>
                  <div className="metric">
                    <span>정치 감정 비율</span>
                    <strong>{ratios[0]?.value ?? 0}%</strong>
                  </div>
                </div>
                <InlineBarPlot data={ratios} />
                <div className="badge">지지와 반대가 얼마나 갈리는지 빠르게 읽기 위한 비율입니다.</div>
              </section>

              <section className="chart-card">
                <div>
                  <h3>최근 정치 핵심</h3>
                  <div className="metric">
                    <span>가장 먼저 볼 글</span>
                    <strong>{truncate(topPostTitle, 14)}</strong>
                  </div>
                </div>
                <div className="mini-summary">
                  <p>정치 탭도 향후에는 경제 탭처럼 감정 있는 글만 다시 골라 비율을 더 정밀하게 계산할 예정입니다.</p>
                  <p>지금은 양극화와 선거 관심도, 지지와 반대의 균형을 보는 용도로 유지합니다.</p>
                  <p>경제 분석과 테이블과 API를 분리해 둔 구조는 그대로 유지됩니다.</p>
                </div>
              </section>
            </div>
          </div>
        </article>

        <aside className="panel summary-card">
          <span className="section-label">오른쪽 요약</span>
          <div className="headline-row single">
            <div>
              <h2>정치 탭 한눈 요약</h2>
              <p>오른쪽 카드에서 비율, 양극화, 선거 관심도, 상위 언급 정치인을 한 번에 보게 정리했습니다.</p>
            </div>
          </div>

          <section className="score-box">
            <span>현재 정치 체감</span>
            <strong>{politicsRegimeLabel(snapshot)}</strong>
            <small>정치 분석은 경제 탭과 완전히 분리된 모듈로 동작합니다.</small>
          </section>

          <div className="summary-lines">
            {buildPoliticsSummary(snapshot, dashboard, sentimentRows, polarizationRows).map((line) => (
              <div className="summary-line" key={line}>
                {line}
              </div>
            ))}
          </div>

          <div className="layout-note">
            참고 소스: DCInside 이재명 마이너 갤러리, 보수주의 마이너 갤러리
          </div>
        </aside>
      </section>
    </>
  );
}

function buildMarketLinePoints(snapshots: DailySnapshot[]): TrendPoint[] {
  return snapshots.length > 0
    ? snapshots.map((item) => ({
        label: shortDate(item.snapshot_date),
        value: item.sentiment_avg,
        secondary: item.fear_greed_avg,
      }))
    : [{ label: "집계 대기", value: 0, secondary: 0 }];
}

function buildPoliticalLinePoints(rows: PoliticalPolarizationPoint[]): TrendPoint[] {
  const items = rows.slice(-30).map((item) => ({
    label: shortDate(item.date),
    value: item.value,
    secondary: item.election_heat ?? undefined,
  }));
  return items.length > 0 ? items : [{ label: "집계 대기", value: 0, secondary: 0 }];
}

function buildHotPostRows(posts: CommunityPost[]): HotPostRow[] {
  return posts
    .filter((post) => !post.analytics_excluded && post.emotional_signal)
    .map((post) => ({
      title: post.title,
      boardName: post.board_name,
      url: post.url,
      publishedAt: post.published_at,
      views: post.view_count ?? 0,
      upvotes: post.upvotes ?? 0,
      comments: post.comment_count ?? 0,
      influence: Math.round(post.influence_score ?? 0),
      status: classifyDisplayTone(post),
      reason: post.influence_reason ?? "반응량과 감정 강도로 상위권에 오른 글",
    }))
    .sort((left, right) => right.influence - left.influence || right.views - left.views);
}

function buildMarketRatios(posts: CommunityPost[]): RatioPoint[] {
  const counts = { positive: 0, negative: 0, neutral: 0 };

  for (const post of posts) {
    const tone = classifyDisplayTone(post);
    if (tone === "긍정") {
      counts.positive += 1;
    } else if (tone === "부정") {
      counts.negative += 1;
    } else {
      counts.neutral += 1;
    }
  }

  const total = posts.length || 1;
  return [
    { label: "긍정", value: Math.round((counts.positive / total) * 100) },
    { label: "부정", value: Math.round((counts.negative / total) * 100) },
    { label: "관망", value: Math.round((counts.neutral / total) * 100) },
  ];
}

function buildPoliticsRatios(rows: PoliticalSentiment[]): RatioPoint[] {
  let support = 0;
  let opposition = 0;
  let neutral = 0;

  for (const row of rows) {
    if (row.support_score >= row.opposition_score + 8 && row.support_score >= 18) {
      support += 1;
    } else if (row.opposition_score >= row.support_score + 8 && row.opposition_score >= 18) {
      opposition += 1;
    } else {
      neutral += 1;
    }
  }

  const total = rows.length || 1;
  return [
    { label: "지지", value: Math.round((support / total) * 100) },
    { label: "반대", value: Math.round((opposition / total) * 100) },
    { label: "유보", value: Math.round((neutral / total) * 100) },
  ];
}

function buildMarketSummary(
  snapshot: DailySnapshot | null,
  posts: CommunityPost[],
  hotPosts: HotPostRow[],
  ratios: RatioPoint[]
) {
  const positive = ratios.find((item) => item.label === "긍정")?.value ?? 0;
  const negative = ratios.find((item) => item.label === "부정")?.value ?? 0;
  const neutral = ratios.find((item) => item.label === "관망")?.value ?? 0;
  const top = hotPosts[0];

  return [
    `최근 30일 동안 감정이 드러난 경제 글은 ${posts.length}건입니다. 긍정 ${positive}%, 부정 ${negative}%, 관망 ${neutral}% 비율입니다.`,
    snapshot
      ? `공포/탐욕 평균은 ${formatScore(snapshot.fear_greed_avg)}, 혐오 평균은 ${formatScore(snapshot.hate_index_avg)}입니다. ${fearGreedMessage(snapshot)}`
      : "30일 스냅샷이 아직 충분하지 않습니다.",
    top
      ? `가장 영향이 큰 글은 '${truncate(top.title, 26)}'이며, 이유는 ${top.reason} 입니다.`
      : "영향 글 집계가 아직 충분하지 않습니다.",
  ];
}

function buildPoliticsSummary(
  snapshot: PoliticalDashboard["sentiment_snapshot"],
  dashboard: PoliticalDashboard,
  sentimentRows: PoliticalSentiment[],
  polarizationRows: PoliticalPolarizationPoint[]
) {
  const ratios = buildPoliticsRatios(sentimentRows);
  const support = ratios.find((item) => item.label === "지지")?.value ?? 0;
  const opposition = ratios.find((item) => item.label === "반대")?.value ?? 0;
  const neutral = ratios.find((item) => item.label === "유보")?.value ?? 0;
  const topPolitician = dashboard.top_politicians[0]?.keyword ?? "집계 대기";
  const latestPolar = polarizationRows[polarizationRows.length - 1];

  return [
    `최근 정치 글 기준으로 지지 ${support}%, 반대 ${opposition}%, 유보 ${neutral}% 입니다.`,
    `가장 많이 언급된 정치인은 ${topPolitician}입니다.`,
    snapshot && latestPolar
      ? `정치 감정 ${formatScore(snapshot.political_sentiment_avg)}, 양극화 ${formatScore(latestPolar.value)}, 선거 관심도 ${formatScore(latestPolar.election_heat)}입니다.`
      : "정치 스냅샷이 아직 충분하지 않습니다.",
  ];
}

function classifyDisplayTone(post: CommunityPost) {
  const text = `${post.title} ${post.body ?? ""}`.toLowerCase();
  const positiveTerms = ["반등", "호황", "호재", "좋다", "기회", "간다", "성공", "매수", "오른다", "상승", "대박"];
  const negativeTerms = ["망", "패닉", "손절", "하락", "불안", "무섭", "위기", "폭락", "붕괴", "최악", "악재", "공포"];
  const positiveHits = positiveTerms.filter((term) => text.includes(term)).length;
  const negativeHits = negativeTerms.filter((term) => text.includes(term)).length;
  const sentimentScore = post.sentiment_score ?? 0;
  const fearGreed = post.fear_greed_score ?? 50;
  const hateIndex = post.hate_index ?? 0;

  if (sentimentScore >= 8 || positiveHits >= 1 || fearGreed >= 58) {
    if (negativeHits === 0 || sentimentScore >= 12) {
      return "긍정";
    }
  }

  if (sentimentScore <= -8 || negativeHits >= 1 || fearGreed <= 42 || hateIndex >= 10) {
    if (positiveHits === 0 || sentimentScore <= -12 || hateIndex >= 10) {
      return "부정";
    }
  }

  return "관망";
}

function marketRegimeLabel(snapshot: DailySnapshot | null) {
  if (!snapshot) {
    return "집계중";
  }
  if (snapshot.fear_greed_avg <= 35) {
    return "공포 우세";
  }
  if (snapshot.fear_greed_avg >= 65) {
    return "환희 우세";
  }
  if (snapshot.hate_index_avg >= 40) {
    return "혐오 과열";
  }
  return "관망권";
}

function marketExperimentLabel(snapshot: DailySnapshot | null) {
  if (!snapshot) {
    return "관찰중";
  }
  if (snapshot.fear_greed_avg <= 35) {
    return "매수 후보";
  }
  if (snapshot.fear_greed_avg >= 65) {
    return "차익 후보";
  }
  return "중립 구간";
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

function fearGreedMessage(snapshot: DailySnapshot) {
  if (snapshot.fear_greed_avg <= 35) {
    return "공포 구간이 강해서 저점 매수 가설을 실험하기 좋은 상태입니다.";
  }
  if (snapshot.fear_greed_avg >= 65) {
    return "환희 구간이 강해서 차익 실현 가설을 점검하기 좋은 상태입니다.";
  }
  return "아직은 공포나 환희로 확실히 쏠리지는 않은 상태입니다.";
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
