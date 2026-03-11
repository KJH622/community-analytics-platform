import { ChartPanel } from "@/components/chart-panel";
import { DomainTabs } from "@/components/domain-tabs";
import { LiveCommunityFeed } from "@/components/live-community-feed";
import { MarketComparisonChart } from "@/components/market-comparison-chart";
import { fetchCommunity, fetchDashboardData, fetchMarketComparison } from "@/lib/api";

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

function formatRatio(value: number | null | undefined) {
  if (value == null) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function formatDateLabel(value: string | null | undefined) {
  if (!value) {
    return "실시간 갱신";
  }
  const date = new Date(value);
  return `${date.getMonth() + 1}월 ${date.getDate()}일 기준`;
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
      label: "CALM",
      tone: "calm",
      badge: "리스크 낮음",
      description: "커뮤니티 긴장도와 지수 변동이 모두 낮아서 비교적 안정적인 구간입니다.",
    };
  }

  if (combinedPressure < 2.2) {
    return {
      label: "WATCH",
      tone: "watch",
      badge: "방향성 관찰",
      description: "지수 변화 또는 커뮤니티 반응이 서서히 올라오는 구간이라 흐름을 더 지켜볼 필요가 있습니다.",
    };
  }

  return {
    label: "ALERT",
    tone: "alert",
    badge: "변동성 확대",
    description: "시장 변동과 커뮤니티 긴장도가 함께 올라온 상태라 단기 위험 신호가 강합니다.",
  };
}

export default async function DashboardPage() {
  const [data, community, market] = await Promise.all([
    fetchDashboardData(),
    fetchCommunity({ topicCategory: "economy", pageSize: 6 }),
    fetchMarketComparison(14),
  ]);

  const latestSnapshot = data.sentiment[0] ?? null;
  const latestIndicator = data.indicators.find((item) => item.latest_release) ?? null;
  const latestHateIndex = market.latest.hate_index ?? latestSnapshot?.hate_index ?? 0;
  const signalState = getSignalState(
    latestHateIndex,
    market.latest.kospi_change_pct,
    market.latest.kosdaq_change_pct
  );
  const highlightPost = community.items[0] ?? null;
  const sourceLine =
    Array.from(
      new Set(
        community.items
          .map((item) => item.source_name ?? item.source_code)
          .filter((value): value is string => Boolean(value))
      )
    ).join(" · ") || "PPOMPPU · CLIEN · BOBAEDREAM";
  const topKeywords = pickKeywords(latestSnapshot?.top_keywords, 4);
  const summaryKeywordText = topKeywords.length ? topKeywords.join(", ") : "시장 키워드 집계 중";
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
    `코스피 ${formatSignedPercent(market.latest.kospi_change_pct)}, 코스닥 ${formatSignedPercent(market.latest.kosdaq_change_pct)} 흐름입니다.`,
    `경제 혐오지수는 ${formatNumber(latestHateIndex, 2)}이고, 상위 키워드는 ${summaryKeywordText} 입니다.`,
    latestIndicator?.latest_release?.actual_value != null
      ? `${latestIndicator.name} 최신 값은 ${latestIndicator.latest_release.actual_value.toLocaleString("ko-KR")}입니다.`
      : "실시간 거시 지표 업데이트를 기다리는 중입니다.",
  ];

  return (
    <main className="dashboard-page dashboard-home">
      <DomainTabs active="market" />

      <section className="dashboard-top-grid">
        <section className="panel market-stage">
          <span className="section-label">MARKET SNAPSHOT</span>

          <div className="dashboard-heading">
            <div>
              <h1>오늘의 시장 흐름</h1>
              <p>시장 지표와 커뮤니티 반응을 한 화면에서 비교합니다.</p>
            </div>
            <span className="dashboard-reference">{formatDateLabel(market.reference_date)}</span>
          </div>

          <div className="market-stage-grid">
            <article className={`signal-hero-card signal-hero-card-${signalState.tone}`}>
              <div className="signal-hero-head">
                <span>오늘의 시장 체감</span>
                <span className="soft-pill">{signalState.badge}</span>
              </div>
              <strong>{signalState.label}</strong>
              <p>{signalState.description}</p>

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
                  <span>상승 비중</span>
                  <b>{formatRatio(latestSnapshot?.bullish_ratio)}</b>
                </div>
              </div>

              <div className="signal-footer">
                <span>핵심 키워드</span>
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
                <p>실제 종가 기준으로 반영됩니다.</p>
              </article>

              <article className="market-tile">
                <div className="market-tile-head">
                  <span>코스닥</span>
                  <span>{formatSignedPercent(market.latest.kosdaq_change_pct)}</span>
                </div>
                <strong>{formatNumber(market.latest.kosdaq_close, 2)}</strong>
                <p>휴장일에는 직전 거래일 종가를 유지합니다.</p>
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
                <p>
                  {latestIndicator
                    ? `${latestIndicator.name} 최신 값을 함께 보여줍니다.`
                    : "연결된 경제 지표가 아직 없습니다."}
                </p>
              </article>
            </div>
          </div>
        </section>

        <aside className="panel market-summary-card">
          <span className="section-label">3-LINE SUMMARY</span>

          <div className="dashboard-heading compact-heading">
            <div>
              <h2>지금 한눈 요약</h2>
              <p>시장과 커뮤니티 분위기를 빠르게 훑을 수 있게 정리했습니다.</p>
            </div>
          </div>

          <section className={`summary-tone-card summary-tone-card-${signalState.tone}`}>
            <span>오늘의 경제 레벨</span>
            <strong>{signalState.label}</strong>
            <p>{signalState.description}</p>
          </section>

          <div className="summary-stack">
            {summaryItems.map((item) => (
              <div className="summary-line" key={item}>
                {item}
              </div>
            ))}
          </div>

          <div className="summary-footnote">
            <span>실시간 출처</span>
            <strong>{sourceLine}</strong>
          </div>
        </aside>
      </section>

      {highlightPost ? (
        <section className="panel story-banner">
          <span className="section-label">LIVE COMMUNITY FEED</span>

          <div className="story-banner-grid">
            <div>
              <h2>{highlightPost.title}</h2>
              <p>{truncateText(highlightPost.body || highlightPost.title, 180)}</p>
              <div className="story-banner-tags">
                <span className="story-badge">{highlightPost.source_name ?? highlightPost.source_code ?? "COMMUNITY"}</span>
                <span className="story-badge">{highlightPost.board_name}</span>
                <span className="story-badge">{formatDateTime(highlightPost.created_at)} 기준</span>
              </div>
            </div>
            <div className="story-banner-side">
              <span>Live from {sourceLine}</span>
              <strong>최신 게시글 제목과 본문, 메타데이터, 감정 지표를 아래에서 바로 확인할 수 있습니다.</strong>
            </div>
          </div>
        </section>
      ) : null}

      <section className="panel dashboard-wide-panel">
        <div className="dashboard-heading">
          <div>
            <h2>코스피 · 코스닥 · 경제 혐오지수</h2>
            <p>세 지표를 실제 값 그대로 놓고 같은 기간 추세를 비교합니다.</p>
          </div>
          <span className="dashboard-reference">{market.comparison_basis}</span>
        </div>
        <MarketComparisonChart data={market.points} />
      </section>

      <section className="insight-grid">
        <ChartPanel
          title="경제 감정 추이"
          description="커뮤니티 감정 점수의 최근 7일 흐름입니다."
          data={sentimentSeries}
          color="#c56a3a"
        />
        <ChartPanel
          title="코스피 7일 흐름"
          description="최근 7개 시점의 코스피 종가 흐름입니다."
          data={kospiSeries}
          color="#17877a"
        />
        <ChartPanel
          title="코스닥 7일 흐름"
          description="최근 7개 시점의 코스닥 종가 흐름입니다."
          data={kosdaqSeries}
          color="#2d61c8"
        />
      </section>

      <section className="panel dashboard-feed-panel">
        <div className="dashboard-heading">
          <div>
            <h2>실시간 경제 게시글</h2>
            <p>실제 크롤 서버가 저장한 경제 게시글을 제목, 본문, 감정 지표와 함께 보여줍니다.</p>
          </div>
          <div className="feed-header-meta">
            <span>누적 {community.total.toLocaleString("ko-KR")}건</span>
            <span>{sourceLine}</span>
          </div>
        </div>

        <LiveCommunityFeed initialPosts={community.items} topicCategory="economy" limit={6} variant="table" />
      </section>
    </main>
  );
}
