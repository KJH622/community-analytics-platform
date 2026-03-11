const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { next: { revalidate: 60 } });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function getJsonNoCache<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function postJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
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
  board_name: string;
  title: string;
  body: string;
  created_at: string;
  view_count: number | null;
  upvotes: number | null;
  downvotes: number | null;
  comment_count: number | null;
  original_url: string;
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
export type PoliticalPost = {
  id: number;
  community_name: string;
  board_name: string | null;
  title: string;
  body: string;
  created_at: string;
  view_count: number | null;
  upvotes: number | null;
  comment_count: number | null;
  original_url: string;
};
export type PoliticsDashboard = {
  indicator_cards: Array<{
    indicator_name: string;
    code: string;
    date: string;
    value: number;
    label: string | null;
    source: string | null;
    unit: string | null;
  }>;
  approval_trend: Array<{
    indicator_name: string;
    code: string;
    date: string;
    value: number;
    label: string | null;
    source: string | null;
    unit: string | null;
  }>;
  party_support_comparison: Array<{
    indicator_name: string;
    code: string;
    date: string;
    value: number;
    label: string | null;
    source: string | null;
    unit: string | null;
  }>;
  politician_mentions_top10: Array<{ name: string; mentions: number }>;
  keyword_trends: Array<{ keyword: string; mentions: number }>;
  political_sentiment_index: Array<{ date: string; value: number }>;
  polarization_index: Array<{ date: string; value: number }>;
  election_heat_index: Array<{ date: string; value: number }>;
  community_posts: PoliticalPost[];
  reference_communities: Array<{
    name: string;
    description: string | null;
    leaning: string | null;
    link: string;
    status: string;
  }>;
};

export async function fetchDashboardData() {
  const [indicators, news, community, sentiment, keywordTrends, topicBreakdown] = await Promise.all([
    getJson<IndicatorLatest[]>("/api/v1/indicators/latest"),
    getJson<{ items: NewsItem[] }>("/api/v1/news?page=1&page_size=5"),
    getJson<{ items: CommunityPost[] }>("/api/v1/community/posts?page=1&page_size=5"),
    getJson<DailySnapshot[]>("/api/v1/analytics/daily-sentiment?limit=7"),
    getJson<KeywordTrend[]>("/api/v1/analytics/keyword-trends?limit=8"),
    getJson<TopicBreakdown[]>("/api/v1/analytics/topic-breakdown"),
  ]);

  return { indicators, news: news.items, community: community.items, sentiment, keywordTrends, topicBreakdown };
}

export async function fetchNews(keyword?: string) {
  const suffix = keyword ? `&keyword=${encodeURIComponent(keyword)}` : "";
  return getJson<{ items: NewsItem[]; total: number; page: number; page_size: number }>(
    `/api/v1/news?page=1&page_size=20${suffix}`
  );
}

export async function fetchCommunity({ boardName, boardId, pageSize = 20 }: CommunityQuery = {}) {
  const parts = [`page=1`, `page_size=${pageSize}`];
  if (boardName) {
    parts.push(`board_name=${encodeURIComponent(boardName)}`);
  }
  if (boardId) {
    parts.push(`board_id=${encodeURIComponent(boardId)}`);
  }
  return getJson<{ items: CommunityPost[]; total: number; page: number; page_size: number }>(
    `/api/v1/community/posts?${parts.join("&")}`
  );
}

export async function fetchCommunityLive(query: CommunityQuery = {}) {
  const { boardName, boardId, pageSize = 20 } = query;
  const parts = [`page=1`, `page_size=${pageSize}`];
  if (boardName) {
    parts.push(`board_name=${encodeURIComponent(boardName)}`);
  }
  if (boardId) {
    parts.push(`board_id=${encodeURIComponent(boardId)}`);
  }
  return getJsonNoCache<{ items: CommunityPost[]; total: number; page: number; page_size: number }>(
    `/api/v1/community/posts?${parts.join("&")}`
  );
}

export async function refreshCommunityLive(boardId = "stockus", maxPosts = 10) {
  const query = new URLSearchParams({
    board_id: boardId,
    max_pages: "1",
    max_posts: String(maxPosts),
  });
  return postJson<{ status: string; board_id: string; records_processed: number; message: string }>(
    `/api/v1/community/refresh-live?${query.toString()}`
  );
}

export async function fetchPoliticsDashboard() {
  return getJson<PoliticsDashboard>("/api/v1/politics/dashboard");
}
