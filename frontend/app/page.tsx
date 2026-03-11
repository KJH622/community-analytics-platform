import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { MarketComparisonChart } from "@/components/market-comparison-chart";
import { CommunityPost, fetchCommunity, fetchDashboardData, fetchMarketComparison } from "@/lib/api";

const KEYWORD_STOPWORDS = new Set([
  "to",
  "of",
  "in",
  "and",
  "the",
  "for",
  "with",
  "from",
  "this",
  "that",
  "ㅋㅋ",
  "ㅋㅋㅋ",
  "ㅋㅋㅋㅋ",
  "ㅎㅎ",
  "ㅎㅎㅎ",
  "오늘",
  "이번",
  "있는",
  "한다",
  "했다",
]);

function formatNumber(value: number | null | undefined, digits = 1) {
  if (value == null) {
    return "-";
  }
  return value.toLocaleString("ko-KR", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatSignedPercent(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function formatSignedPoint(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}p`;
}

function formatDateTime(value: string | null | undefined) {
  if (!value) {
    return "방금 갱신";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatReferenceDate(value: string | null | undefined) {
  if (!value) {
    return "실시간 갱신";
  }
  const date = new Date(value);
  return `${date.getMonth() + 1}월 ${date.getDate()}일 기준`;
}

function truncateText(value: string | null | undefined, length = 150) {
  if (!value) {
    return "";
  }
  if (value.length <= length) {
    return value;
  }
  return `${value.slice(0, length).trim()}...`;
}

function pickKeywords(keywords: string[] | undefined, limit = 4) {
  return (keywords ?? [])
    .map((keyword) => keyword.trim())
    .filter((keyword) => keyword.length > 1)
    .filter((keyword) => !KEYWORD_STOPWORDS.has(keyword.toLowerCase()))
    .slice(0, limit);
}

function getSignalState(
  hateIndex: number,
  kospiChangePct: number | null | undefined,
  kosdaqChangePct: number | null | undefined
) {
  const downsidePressure = Math.max(0, -(kospiChangePct ?? 0)) + Math.max(0, -(kosdaqChangePct ?? 0));
  const combinedPressure = hateIndex + downsidePressure * 0.35;

  if (combinedPressure < 1.1) {
    return {
      label: "안정",
      tone: "calm",
      badge: "리스크 낮음",
    };
  }

  if (combinedPressure < 2.2) {
    return {
      label: "주시",
      tone: "watch",
      badge: "방향성 관찰",
    };
  }

  return {
    label: "경계",
    tone: "alert",
    badge: "변동성 확대",
  };
}

function getAnalysis(post: CommunityPost) {
  if (post.analysis) {
    return post.analysis;
  }

  return {
    sentiment_score: post.sentiment_score ?? 0,
    fear_greed_score: post.fear_greed_score ?? 50,
    hate_index: post.hate_index ?? 0,
    uncertainty_score: post.uncertainty_score ?? 0,
    market_bias: post.market_bias ?? "neutral",
    keywords: post.keywords ?? [],
    topics: [],
    entities: [],
  };
}

function getImpactScore(post: CommunityPost) {
  const analysis = getAnalysis(post);
  return analysis.hate_index * 5 + (post.comment_count ?? 0) * 0.7 + (post.view_count ?? 0) / 900;
}

export default async function DashboardPage() {
  const [data, community, market] = await Promise.all([
    fetchDashboardData(),
    fetchCommunity({ topicCategory: "economy", pageSize: 6 }),
    fetchMarketComparison(14),
  ]);

  const latestSnapshot = data.sentiment[0] ?? null;
  const filteredCommunityItems = community.items.filter(
    (item) => !/(전월세 감소폭|서울 전월세)/.test(item.title) && !/(전월세 감소폭|서울 전월세)/.test(item.body)
  );
  const visibleCommunityItems = filteredCommunityItems.length ? filteredCommunityItems : community.items;
  const latestIndicator = data.indicators.find((item) => item.latest_release) ?? null;
  const latestHateIndex = market.latest.hate_index ?? latestSnapshot?.hate_index ?? 0;
  const signalState = getSignalState(
    latestHateIndex,
    market.latest.kospi_change_pct,
    market.latest.kosdaq_change_pct
  );
  const sourceLine =
    Array.from(
      new Set(
        visibleCommunityItems
          .map((item) => item.source_name ?? item.source_code)
          .filter((value): value is string => Boolean(value))
      )
    ).join(" · ") || "PPOMPPU · CLIEN · BOBAEDREAM";
  const feedKeywords = Array.from(
    new Set(
      visibleCommunityItems.flatMap((item) => pickKeywords(getAnalysis(item).keywords, 8))
    )
  ).slice(0, 4);
  const topKeywords = pickKeywords(latestSnapshot?.top_keywords, 4);
  const summaryKeywordText = (feedKeywords.length ? feedKeywords : topKeywords).join(", ") || "시장 이슈 집계 중";
  const leadPost =
    visibleCommunityItems
      .slice()
      .sort((left, right) => getImpactScore(right) - getImpactScore(left))[0] ?? null;
  const recentMarketPoints = market.points.slice(-7);
  const kospiSeries = recentMarketPoints
    .filter((item) => item.kospi_close != null)
    .map((item) => ({ label: item.date.slice(5), value: item.kospi_close ?? 0 }));
  const kosdaqSeries = recentMarketPoints
    .filter((item) => item.kosdaq_close != null)
    .map((item) => ({ label: item.date.slice(5), value: item.kosdaq_close ?? 0 }));
  const sentimentSeries = data.sentiment
    .slice()
    .reverse()
    .map((item) => ({
      label: item.snapshot_date.slice(5),
      value: item.sentiment_score,
    }));
  const summaryItems = [
    leadPost
      ? `혐오지수 ${formatNumber(latestHateIndex, 2)}은 ${summaryKeywordText} 관련 글이 많았고, '${truncateText(leadPost.title, 34)}' 같은 게시글 반응이 크게 반영된 값입니다.`
      : `혐오지수 ${formatNumber(latestHateIndex, 2)}은 ${summaryKeywordText} 관련 언급이 반영된 값입니다.`,
    `코스피 ${formatSignedPercent(market.latest.kospi_change_pct)} / 코스닥 ${formatSignedPercent(market.latest.kosdaq_change_pct)} 흐름입니다.`,
    latestIndicator?.latest_release?.actual_value != null
      ? `${latestIndicator.name} 최신 값은 ${latestIndicator.latest_release.actual_value.toLocaleString("ko-KR")}입니다.`
      : "실시간 거시 지표 업데이트를 기다리는 중입니다.",
  ];

  return (
    <main className="dashboard-page dashboard-home">
      <DomainTabs active="market" />

      <section className="dashboard-top-grid">
        <div className="top-main-stack">
          <section className="panel market-stage">
            <span className="section-label">MARKET SNAPSHOT</span>

            <div className="dashboard-heading">
              <div>
                <h1>오늘의 시장 흐름</h1>
              </div>
              <span className="dashboard-reference">{formatReferenceDate(market.reference_date)}</span>
            </div>

            <div className="market-stage-grid">
              <article className={`signal-hero-card signal-hero-card-${signalState.tone}`}>
                <div className="signal-hero-head">
                  <span>오늘의 시장 체감</span>
                  <span className="soft-pill">{signalState.badge}</span>
                </div>
                <strong>{signalState.label}</strong>

                <div className="signal-data-grid">
                  <div>
                    <span>경제 혐오지수</span>
                    <b>{formatNumber(latestHateIndex, 2)}</b>
                  </div>
                  <div>
                    <span>공포/탐욕</span>
                    <b>{formatNumber(latestSnapshot?.fear_greed_score, 1)}</b>
                  </div>
                  <div>
                    <span>핵심 키워드</span>
                    <b>{summaryKeywordText.split(",")[0] ?? "집계중"}</b>
                  </div>
                </div>

                <div className="signal-footer">
                  <div className="chip-row">
                    {(topKeywords.length ? topKeywords : ["데이터", "집계", "중"]).map((keyword) => (
                      <span className="keyword-chip" key={keyword}>
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              </article>

              <div className="market-stage-side">
                <article className="market-tile">
                  <div className="market-tile-head">
                    <span>코스피</span>
                    <span>{formatSignedPercent(market.latest.kospi_change_pct)}</span>
                  </div>
                  <strong>{formatNumber(market.latest.kospi_close, 2)}</strong>
                </article>

                <article className="market-tile">
                  <div className="market-tile-head">
                    <span>코스닥</span>
                    <span>{formatSignedPercent(market.latest.kosdaq_change_pct)}</span>
                  </div>
                  <strong>{formatNumber(market.latest.kosdaq_close, 2)}</strong>
                </article>

                <article className="market-tile market-tile-wide">
                  <div className="market-tile-head">
                    <span>최근 발표 지표</span>
                    <span>{latestIndicator?.country ?? "GLOBAL"}</span>
                  </div>
                  <strong>
                    {latestIndicator?.latest_release?.actual_value != null
                      ? latestIndicator.latest_release.actual_value.toLocaleString("ko-KR")
                      : "-"}
                  </strong>
                  {latestIndicator ? <span className="market-tile-note">{latestIndicator.name}</span> : null}
                </article>
              </div>
            </div>
          </section>

          <section className="panel dashboard-feed-panel">
            <div className="dashboard-heading">
              <div>
                <h2>실시간 경제 게시글</h2>
              </div>
              <div className="feed-header-meta">
                <span>누적 {community.total.toLocaleString("ko-KR")}건</span>
                <span>{sourceLine}</span>
              </div>
            </div>

            <LiveCommunityFeed initialPosts={visibleCommunityItems} topicCategory="economy" limit={6} variant="table" />
          </section>
        </div>

        <aside className="panel market-summary-card">
          <span className="section-label">3-LINE SUMMARY</span>

          <div className="dashboard-heading compact-heading">
            <div>
              <h2>지금 한눈 요약</h2>
            </div>
          </div>

          <section className={`summary-tone-card summary-tone-card-${signalState.tone}`}>
            <span>오늘의 경제 레벨</span>
            <strong>{signalState.label}</strong>
          </section>

          <div className="summary-stack">
            {summaryItems.map((item) => (
              <div className="summary-line" key={item}>
                {item}
              </div>
            ))}
          </div>

          <div className="summary-footnote">
            <span>실시간 수집원</span>
            <strong>{sourceLine}</strong>
          </div>
        </aside>
      </section>

      <section className="panel dashboard-wide-panel">
        <div className="dashboard-heading">
          <div>
            <h2>코스피 · 코스닥 · 경제 혐오지수</h2>
          </div>
          <span className="dashboard-reference">{market.comparison_basis}</span>
        </div>
        <MarketComparisonChart data={market.points} />
      </section>

      <section className="insight-grid">
        <ChartPanel
          title="경제 감정 추이"
          data={sentimentSeries}
          color="#c56a3a"
        />
        <ChartPanel
          title="코스피 7일 흐름"
          data={kospiSeries}
          color="#17877a"
        />
        <ChartPanel
          title="코스닥 7일 흐름"
          data={kosdaqSeries}
          color="#2d61c8"
        />
      </section>
    </main>
  );
}
