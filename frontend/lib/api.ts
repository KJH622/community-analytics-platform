export type IndicatorRelease = {
  actual_value: number | null;
  release_date: string;
  previous_value: number | null;
};

export type Indicator = {
  id: number;
  code: string;
  name: string;
  category: string;
  country: string;
  unit: string | null;
  latest_release: IndicatorRelease | null;
};

export type DailySnapshot = {
  id: number;
  snapshot_date: string;
  sentiment_avg: number;
  fear_greed_avg: number;
  hate_index_avg: number;
  uncertainty_avg: number;
  bullish_ratio: number;
  bearish_ratio: number;
  neutral_ratio: number;
  top_keywords: string[] | null;
};

export type KeywordTrend = {
  date?: string;
  keyword: string;
  count: number;
};

export type TopicBreakdown = {
  topic: string;
  count: number;
};

export type NewsItem = {
  id: number;
  title: string;
  summary: string | null;
  published_at: string | null;
  category: string | null;
  url: string;
};

export type CommunityPost = {
  id: number;
  title: string;
  board_name: string;
  body: string | null;
  published_at: string | null;
  view_count: number | null;
  upvotes: number | null;
  comment_count: number | null;
  url: string;
  sentiment_score?: number | null;
  fear_greed_score?: number | null;
  hate_index?: number | null;
  uncertainty_score?: number | null;
  market_bias?: string | null;
  analytics_excluded?: boolean;
  exclusion_reasons?: string[] | null;
  emotional_signal?: boolean;
  emotional_reasons?: string[] | null;
  influence_score?: number | null;
  influence_reason?: string | null;
};

export type PoliticalDashboard = {
  sentiment_snapshot: {
    snapshot_date: string;
    political_sentiment_avg: number;
    political_polarization_index: number;
    election_heat_index: number;
    top_keywords: string[] | null;
    top_politicians: string[] | null;
    post_count: number;
  } | null;
  indicators: Array<{
    id: number;
    code: string;
    indicator_name: string;
    values?: Array<{
      date: string;
      value: number;
      label: string | null;
      unit: string | null;
    }>;
  }>;
  top_politicians: Array<{ keyword: string; count: number }>;
  keyword_trends: Array<{ keyword: string; count: number }>;
  posts: Array<{
    id: number;
    community_name: string;
    board_name: string;
    title: string;
    published_at: string | null;
    view_count: number | null;
    upvotes: number | null;
    comment_count: number | null;
    url: string;
    political_sentiment_score?: number | null;
    political_polarization_index?: number | null;
    analytics_excluded?: boolean;
    exclusion_reasons?: string[] | null;
    influence_score?: number | null;
  }>;
  community_references: Array<{
    name: string;
    description: string | null;
    leaning: string | null;
    link: string | null;
  }>;
};

export type PoliticalSentiment = {
  support_score: number;
  opposition_score: number;
  anger_score: number;
  sarcasm_score: number;
  apathy_score: number;
  enthusiasm_score: number;
  election_heat_index: number;
};

export type PoliticalPolarizationPoint = {
  date: string;
  value: number;
  election_heat: number | null;
};

const API_BASE_URL =
  process.env.FRONTEND_API_BASE_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

async function fetchJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API request failed: ${path}`);
  }
  return (await response.json()) as T;
}

export async function getMarketDashboardData() {
  const [indicators, snapshots, keywords, topics, news] = await Promise.all([
    fetchJSON<Indicator[]>("/api/v1/indicators/latest"),
    fetchJSON<DailySnapshot[]>("/api/v1/analytics/daily-sentiment?source_kind=community&limit=30"),
    fetchJSON<KeywordTrend[]>("/api/v1/analytics/keyword-trends?limit=12"),
    fetchJSON<TopicBreakdown[]>("/api/v1/analytics/topic-breakdown"),
    fetchJSON<{ items: NewsItem[] }>("/api/v1/news?limit=6"),
  ]);

  return { indicators, snapshots, keywords, topics, news: news.items };
}

export async function getKoreanMarketCommunityPosts(limit = 12) {
  const dateFrom = new Date();
  dateFrom.setDate(dateFrom.getDate() - 29);
  const dateString = dateFrom.toISOString().slice(0, 10);
  return fetchJSON<{ items: CommunityPost[]; total: number }>(
    `/api/v1/community/posts?source=ppomppu_stock_hot&limit=${limit}&sort=influence&date_from=${dateString}&only_emotional=true`
  );
}

export async function getPoliticsDashboardData() {
  return fetchJSON<PoliticalDashboard>("/api/v1/politics/dashboard");
}

export async function getPoliticsSentiment() {
  return fetchJSON<PoliticalSentiment[]>("/api/v1/politics/sentiment");
}

export async function getPoliticsPolarization() {
  return fetchJSON<PoliticalPolarizationPoint[]>("/api/v1/politics/polarization");
}

export async function getNews(query = "") {
  return fetchJSON<{ items: NewsItem[]; total: number }>(`/api/v1/news${query}`);
}

export async function getCommunityPosts(query = "") {
  return fetchJSON<{ items: CommunityPost[]; total: number }>(`/api/v1/community/posts${query}`);
}
