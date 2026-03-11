const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

type PageResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

async function getJson<T>(path: string, cache: RequestCache = "force-cache"): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
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
  return getJson<PageResponse<CommunityPost>>(`/api/v1/community/posts?${parts.join("&")}`, "no-store").catch(() =>
    emptyPage<CommunityPost>(pageSize)
  );
}
