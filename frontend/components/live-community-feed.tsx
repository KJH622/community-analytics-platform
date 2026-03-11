"use client";

import { useEffect, useState, useTransition } from "react";

import { CommunityPost, fetchCommunityLive } from "@/lib/api";

type LiveCommunityFeedProps = {
  initialPosts: CommunityPost[];
  boardId?: string;
  boardName?: string;
  sourceCode?: string;
  topicCategory?: "economy" | "politics";
  variant?: "table" | "list";
  limit?: number;
};

export function LiveCommunityFeed({
  initialPosts,
  boardId,
  boardName,
  sourceCode,
  topicCategory,
  variant = "list",
  limit = 10,
}: LiveCommunityFeedProps) {
  const [posts, setPosts] = useState(initialPosts);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setPosts(initialPosts);
  }, [initialPosts]);

  useEffect(() => {
    const refreshFeed = async () => {
      try {
        setError(null);
        const latest = await fetchCommunityLive({
          boardId,
          boardName,
          sourceCode,
          topicCategory,
          pageSize: limit,
        });
        startTransition(() => {
          setPosts(latest.items);
          setLastUpdated(new Date());
        });
      } catch {
        setError("지금은 최신 게시글을 다시 불러오지 못하고 있습니다.");
      }
    };

    void refreshFeed();
    const timer = window.setInterval(() => {
      void refreshFeed();
    }, 60_000);

    return () => window.clearInterval(timer);
  }, [boardId, boardName, limit, sourceCode, startTransition, topicCategory]);

  const statusText = isPending ? "최신 글을 확인하는 중..." : "실시간 커뮤니티 피드";
  const updateText = lastUpdated
    ? `${lastUpdated.toLocaleTimeString("ko-KR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })} 갱신`
    : "60초마다 자동 갱신";

  if (variant === "table") {
    return (
      <div className="live-feed">
        <div className="live-feed-meta">
          <span>{statusText}</span>
          <span>{updateText}</span>
        </div>
        {error ? <div className="live-feed-error">{error}</div> : null}
        {!posts.length ? <div className="live-feed-error">표시할 경제 게시글이 아직 없습니다.</div> : null}

        <div className="community-grid" role="list" aria-label="커뮤니티 게시글 목록">
          {posts.map((post) => {
            const analysis = getAnalysis(post);

            return (
              <article className="community-card" key={post.id}>
                <div className="community-card-top">
                  <div className="community-source-line">
                    <span className="story-badge">{post.source_name ?? post.source_code ?? "COMMUNITY"}</span>
                    <span>{post.board_name}</span>
                    <span>{formatTime(post.created_at)}</span>
                  </div>

                  <div className={`hate-pill hate-pill-${getHateTone(analysis.hate_index)}`}>
                    혐오 {analysis.hate_index.toFixed(2)}
                  </div>
                </div>

                <a className="community-title-link" href={post.original_url} target="_blank" rel="noreferrer">
                  <h3>{post.title}</h3>
                </a>

                <p className="community-body">{truncate(post.body || post.title, 120)}</p>

                <div className="community-meters">
                  <MetricBar
                    label="혐오지수"
                    value={analysis.hate_index}
                    maxValue={3}
                    tone={getHateTone(analysis.hate_index)}
                  />
                  <MetricBar
                    label="불확실성"
                    value={analysis.uncertainty_score}
                    maxValue={3}
                    tone={getUncertaintyTone(analysis.uncertainty_score)}
                  />
                  <MetricBar
                    label="공포 / 탐욕"
                    value={analysis.fear_greed_score}
                    maxValue={100}
                    tone={getBiasTone(analysis.market_bias)}
                  />
                </div>

                <div className="community-card-bottom">
                  <div className="community-meta">
                    <span>조회 {post.view_count ?? 0}</span>
                    <span>댓글 {post.comment_count ?? 0}</span>
                    <span>추천 {post.upvotes ?? 0}</span>
                  </div>

                  <div className="community-tags">
                    <span className="signal-badge">{getBiasLabel(analysis.market_bias)}</span>
                    {analysis.keywords.slice(0, 3).map((keyword) => (
                      <span className="keyword-chip" key={`${post.id}-${keyword}`}>
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="live-feed">
      <div className="live-feed-meta">
        <span>{statusText}</span>
        <span>{updateText}</span>
      </div>
      {error ? <div className="live-feed-error">{error}</div> : null}
      {!posts.length ? <div className="live-feed-error">표시할 경제 게시글이 아직 없습니다.</div> : null}

      <div className="list">
        {posts.map((item) => {
          const analysis = getAnalysis(item);

          return (
            <a className="list-item" href={item.original_url} key={item.id} target="_blank" rel="noreferrer">
              <div className="list-meta">
                {(item.source_name ?? item.source_code ?? "COMMUNITY")} / {item.board_name} / 조회 {item.view_count ?? 0}
              </div>

              <div className="list-headline">
                <strong>{item.title}</strong>
                <span className={`hate-pill hate-pill-${getHateTone(analysis.hate_index)}`}>
                  혐오 {analysis.hate_index.toFixed(2)}
                </span>
              </div>

              <p>{truncate(item.body || item.title, 180)}</p>

              <div className="inline-analysis">
                <span>{getBiasLabel(analysis.market_bias)}</span>
                <span>불확실성 {analysis.uncertainty_score.toFixed(2)}</span>
                <span>키워드 {analysis.keywords.slice(0, 2).join(", ") || "-"}</span>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function MetricBar({
  label,
  value,
  maxValue,
  tone,
}: {
  label: string;
  value: number;
  maxValue: number;
  tone: string;
}) {
  const width = Math.max(8, Math.min(100, (Math.max(0, value) / maxValue) * 100));

  return (
    <div className="metric-bar">
      <div className="metric-bar-head">
        <span>{label}</span>
        <strong>{value.toFixed(2)}</strong>
      </div>
      <div className="metric-bar-track">
        <div className={`metric-bar-fill metric-bar-fill-${tone}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

function truncate(value: string, length: number) {
  if (value.length <= length) {
    return value;
  }
  return `${value.slice(0, length).trim()}...`;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function getHateTone(value: number) {
  if (value >= 2) {
    return "high";
  }
  if (value >= 1) {
    return "mid";
  }
  return "low";
}

function getUncertaintyTone(value: number) {
  if (value >= 2) {
    return "high";
  }
  if (value >= 0.8) {
    return "mid";
  }
  return "low";
}

function getBiasTone(value: string) {
  if (value === "bullish") {
    return "up";
  }
  if (value === "bearish") {
    return "down";
  }
  return "mid";
}

function getBiasLabel(value: string) {
  if (value === "bullish") {
    return "강세";
  }
  if (value === "bearish") {
    return "약세";
  }
  return "중립";
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
