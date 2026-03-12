function getApiBase() {
  if (typeof window === "undefined") {
    return process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
}

type PageResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

async function getJson<T>(path: string, cache: RequestCache = "force-cache"): Promise<T> {
  const response = await fetch(`${getApiBase()}${path}`, {
    cache,
    next: cache === "force-cache" ? { revalidate: 60 } : undefined,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} for ${path}`);
  }
  return response.json() as Promise<T>;
}

function emptyPage<T>(pageSize: number): PageResponse<T> {
  return { items: [], total: 0, page: 1, page_size: pageSize };
}

export type IndicatorLatest = {
  code: string;
  name: string;
  country: string;
  category: string;
  unit: string | null;
  latest_release: {
    release_date: string;
    actual_value: number | null;
    previous_value: number | null;
    forecast_value: number | null;
  } | null;
};

export type NewsItem = {
  id: number;
  title: string;
  body: string;
  publisher: string | null;
  canonical_url: string;
  category: string | null;
  tags: string[];
  published_at: string;
};

export type CommunityPost = {
  id: number;
  source_code?: string | null;
  source_name?: string | null;
  board_code?: string | null;
  board_name: string;
  topic_category?: string | null;
  title: string;
  body: string;
  created_at: string;
  author_hash?: string | null;
  view_count: number | null;
  upvotes: number | null;
  downvotes: number | null;
  comment_count: number | null;
  original_url: string;
  sentiment_score?: number;
  fear_greed_score?: number;
  hate_index?: number;
  uncertainty_score?: number;
  market_bias?: string;
  keywords?: string[];
  analysis?: {
    sentiment_score: number;
    fear_greed_score: number;
    hate_index: number;
    uncertainty_score: number;
    market_bias: string;
    keywords: string[];
    topics: string[];
    entities: string[];
  };
};

type CommunityQuery = {
  boardName?: string;
  boardId?: string;
  sourceCode?: string;
  topicCategory?: "economy" | "politics";
  pageSize?: number;
};

export type DailySnapshot = {
  snapshot_date: string;
  country: string;
  sentiment_score: number;
  fear_greed_score: number;
  hate_index: number;
  uncertainty_score: number;
  bullish_ratio: number;
  bearish_ratio: number;
  neutral_ratio: number;
  top_keywords: string[];
};

export type KeywordTrend = { keyword: string; mentions: number };
export type TopicBreakdown = { topic: string; documents: number };

export type MarketComparisonLatest = {
  kospi_close: number | null;
  kosdaq_close: number | null;
  kospi_change_pct: number | null;
  kosdaq_change_pct: number | null;
  hate_index: number | null;
  hate_change: number | null;
};

export type MarketComparisonPoint = {
  date: string;
  kospi_close: number | null;
  kosdaq_close: number | null;
  hate_index: number;
  kospi_is_carried: boolean;
  kosdaq_is_carried: boolean;
};

export type MarketComparison = {
  reference_date: string | null;
  comparison_basis: string;
  latest: MarketComparisonLatest;
  points: MarketComparisonPoint[];
};

export type PoliticsSummary = {
  reference_date: string | null;
  post_count: number;
  today_post_count: number;
  community_count: number;
  top_issue: string | null;
  top_politician: string | null;
};

export type PoliticsPolarizationPoint = {
  date: string;
  support_rate: number;
  oppose_rate: number;
  neutral_rate: number;
  mentions: number;
};

export type PoliticsEmotion = {
  date: string | null;
  anger_pct: number;
  positive_pct: number;
  neutral_pct: number;
  mentions: number;
};

export type PoliticsIssueSentiment = {
  issue: string;
  mentions: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
};

export type PoliticsIssueSourceReaction = {
  source_code: string;
  source_name: string;
  mentions: number;
  support_pct: number;
  oppose_pct: number;
  neutral_pct: number;
};

export type PoliticsIssueComparison = {
  issue: string;
  sources: PoliticsIssueSourceReaction[];
};

export type PoliticsPoliticianRanking = {
  name: string;
  mentions: number;
};

export type PoliticsTimelineEvent = {
  date: string;
  issue: string;
  headline: string;
  mentions: number;
};

export type PoliticsHotPost = {
  id: number;
  source_code: string;
  source_name: string;
  board_name: string;
  title: string;
  body: string;
  created_at: string;
  view_count: number | null;
  upvotes: number | null;
  comment_count: number | null;
  original_url: string;
  issue_labels: string[];
  stance: string;
  emotion: string;
  influence_score: number;
};

export type PoliticsDashboard = {
  reference_date: string | null;
  summary: PoliticsSummary;
  polarization_trend: PoliticsPolarizationPoint[];
  today_emotion: PoliticsEmotion;
  issue_sentiments: PoliticsIssueSentiment[];
  issue_source_comparisons: PoliticsIssueComparison[];
  politician_rankings: PoliticsPoliticianRanking[];
  issue_timeline: PoliticsTimelineEvent[];
  hot_posts: PoliticsHotPost[];
};

export async function fetchDashboardData() {
  const [indicators, news, community, sentiment, keywordTrends, topicBreakdown] = await Promise.all([
    getJson<IndicatorLatest[]>("/api/v1/indicators/latest").catch(() => []),
    getJson<PageResponse<NewsItem>>("/api/v1/news?page=1&page_size=5").catch(() => emptyPage<NewsItem>(5)),
    getJson<PageResponse<CommunityPost>>("/api/v1/community/posts?page=1&page_size=8").catch(() =>
      emptyPage<CommunityPost>(8)
    ),
    getJson<DailySnapshot[]>("/api/v1/analytics/daily-sentiment?limit=7").catch(() => []),
    getJson<KeywordTrend[]>("/api/v1/analytics/keyword-trends?limit=8").catch(() => []),
    getJson<TopicBreakdown[]>("/api/v1/analytics/topic-breakdown").catch(() => []),
  ]);

  return { indicators, news: news.items, community: community.items, sentiment, keywordTrends, topicBreakdown };
}

export async function fetchNews(keyword?: string) {
  const suffix = keyword ? `&keyword=${encodeURIComponent(keyword)}` : "";
  return getJson<PageResponse<NewsItem>>(`/api/v1/news?page=1&page_size=20${suffix}`).catch(() =>
    emptyPage<NewsItem>(20)
  );
}

export async function fetchCommunity({
  boardName,
  boardId,
  sourceCode,
  topicCategory,
  pageSize = 20,
}: CommunityQuery = {}) {
  const parts = [`page=1`, `page_size=${pageSize}`];
  if (boardName) {
    parts.push(`board_name=${encodeURIComponent(boardName)}`);
  }
  if (boardId) {
    parts.push(`board_id=${encodeURIComponent(boardId)}`);
  }
  if (sourceCode) {
    parts.push(`source_code=${encodeURIComponent(sourceCode)}`);
  }
  if (topicCategory) {
    parts.push(`topic_category=${encodeURIComponent(topicCategory)}`);
  }
  return getJson<PageResponse<CommunityPost>>(`/api/v1/community/posts?${parts.join("&")}`).catch(() =>
    emptyPage<CommunityPost>(pageSize)
  );
}

export async function fetchCommunityLive(query: CommunityQuery = {}) {
  const { boardName, boardId, sourceCode, topicCategory, pageSize = 20 } = query;
  const parts = [`page=1`, `page_size=${pageSize}`];
  if (boardName) {
    parts.push(`board_name=${encodeURIComponent(boardName)}`);
  }
  if (boardId) {
    parts.push(`board_id=${encodeURIComponent(boardId)}`);
  }
  if (sourceCode) {
    parts.push(`source_code=${encodeURIComponent(sourceCode)}`);
  }
  if (topicCategory) {
    parts.push(`topic_category=${encodeURIComponent(topicCategory)}`);
  }
  return getJson<PageResponse<CommunityPost>>(`/api/v1/community/posts?${parts.join("&")}`, "no-store");
}

const emptyMarketComparison: MarketComparison = {
  reference_date: null,
  comparison_basis: "실제 종가 기준, 휴장일은 직전 거래일 종가를 유지합니다.",
  latest: {
    kospi_close: null,
    kosdaq_close: null,
    kospi_change_pct: null,
    kosdaq_change_pct: null,
    hate_index: null,
    hate_change: null,
  },
  points: [],
};

export async function fetchMarketComparison(days = 14): Promise<MarketComparison> {
  const payload: Partial<MarketComparison> = await getJson<Partial<MarketComparison>>(
    `/api/v1/market/comparison?days=${days}`,
    "no-store"
  ).catch(() => ({}));
  return {
    ...emptyMarketComparison,
    ...payload,
    latest: {
      ...emptyMarketComparison.latest,
      ...(payload.latest ?? {}),
    },
    points: payload.points ?? emptyMarketComparison.points,
  };
}

const emptyPoliticsDashboard: PoliticsDashboard = {
  reference_date: null,
  summary: {
    reference_date: null,
    post_count: 0,
    today_post_count: 0,
    community_count: 0,
    top_issue: null,
    top_politician: null,
  },
  polarization_trend: [],
  today_emotion: {
    date: null,
    anger_pct: 0,
    positive_pct: 0,
    neutral_pct: 0,
    mentions: 0,
  },
  issue_sentiments: [],
  issue_source_comparisons: [],
  politician_rankings: [],
  issue_timeline: [],
  hot_posts: [],
};

export async function fetchPoliticsDashboard(): Promise<PoliticsDashboard> {
  const payload: Partial<PoliticsDashboard> = await getJson<Partial<PoliticsDashboard>>(
    "/api/v1/politics/dashboard",
    "no-store"
  ).catch(() => ({}));
  return {
    ...emptyPoliticsDashboard,
    ...payload,
    summary: {
      ...emptyPoliticsDashboard.summary,
      ...(payload.summary ?? {}),
    },
    today_emotion: {
      ...emptyPoliticsDashboard.today_emotion,
      ...(payload.today_emotion ?? {}),
    },
    polarization_trend: payload.polarization_trend ?? emptyPoliticsDashboard.polarization_trend,
    issue_sentiments: payload.issue_sentiments ?? emptyPoliticsDashboard.issue_sentiments,
    issue_source_comparisons: payload.issue_source_comparisons ?? emptyPoliticsDashboard.issue_source_comparisons,
    politician_rankings: payload.politician_rankings ?? emptyPoliticsDashboard.politician_rankings,
    issue_timeline: payload.issue_timeline ?? emptyPoliticsDashboard.issue_timeline,
    hot_posts: payload.hot_posts ?? emptyPoliticsDashboard.hot_posts,
  };
}
