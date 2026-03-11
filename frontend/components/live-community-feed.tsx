"use client";

import { useEffect, useState, useTransition } from "react";

import { CommunityPost, fetchCommunityLive } from "@/lib/api";

type LiveCommunityFeedProps = {
  initialPosts: CommunityPost[];
  boardId?: string;
  boardName?: string;
  variant?: "table" | "list";
  limit?: number;
};

export function LiveCommunityFeed({
  initialPosts,
  boardId = "stockus",
  boardName,
  variant = "list",
  limit = 10,
}: LiveCommunityFeedProps) {
  const [posts, setPosts] = useState(initialPosts);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    const refreshFeed = async () => {
      try {
        setError(null);
        const latest = await fetchCommunityLive({ boardId, boardName, pageSize: limit });
        startTransition(() => {
          setPosts(latest.items);
          setLastUpdated(new Date());
        });
      } catch {
        setError("최신 수집 결과를 불러오지 못했습니다.");
      }
    };

    void refreshFeed();
    const timer = window.setInterval(() => {
      void refreshFeed();
    }, 5 * 60_000);
    return () => window.clearInterval(timer);
  }, [boardId, boardName, limit, startTransition]);

  const statusText = isPending ? "최신 수집 결과를 확인하는 중입니다." : "실시간 수집 결과를 반영하고 있습니다.";
  const updatedText = lastUpdated
    ? `${lastUpdated.toLocaleTimeString("ko-KR")} 기준 갱신`
    : "5분 주기로 자동 갱신";

  if (variant === "table") {
    return (
      <div className="live-feed">
        <div className="live-feed-meta">
          <span>{statusText}</span>
          <span>{updatedText}</span>
        </div>
        {error ? <div className="live-feed-error">{error}</div> : null}
        <div className="community-grid" role="list" aria-label="최신 수집 커뮤니티 게시물 목록">
          {posts.map((post) => {
            const analysis = getAnalysis(post);
            return (
              <article className="community-card" key={post.id}>
                <div className="community-card-top">
                  <div className="community-time">{formatTime(post.created_at)}</div>
                  <div className={`hate-pill hate-pill-${getHateTone(analysis.hate_index)}`}>
                    혐오 지수 {analysis.hate_index.toFixed(1)}
                  </div>
                </div>

                <a className="community-title-link" href={post.original_url} target="_blank" rel="noreferrer">
                  <h3>{post.title}</h3>
                </a>

                <p className="community-body">{truncate(post.body, 140)}</p>

                <div className="community-meters">
                  <MetricBar label="혐오" value={analysis.hate_score} tone={getHateTone(analysis.hate_score)} />
                  <MetricBar
                    label="불확실성"
                    value={analysis.uncertainty_score}
                    tone={getUncertaintyTone(analysis.uncertainty_score)}
                  />
                  <MetricBar
                    label="공포/탐욕"
                    value={analysis.fear_greed_score}
                    tone={getBiasTone(analysis.market_bias)}
                  />
                </div>

                <div className="community-card-bottom">
                  <div className="community-meta">
                    <span>{post.board_name}</span>
                    <span>조회 {post.view_count ?? 0}</span>
                    <span>댓글 {post.comment_count ?? 0}</span>
                    <span>추천 {post.upvotes ?? 0}</span>
                  </div>
                  <div className="community-tags">
                    <span className="signal-badge">{getBiasLabel(analysis.market_bias)}</span>
                    {analysis.tags.map((tag) => (
                      <span className="keyword-chip" key={`${post.id}-${tag}`}>
                        #{tag}
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
        <span>{updatedText}</span>
      </div>
      {error ? <div className="live-feed-error">{error}</div> : null}
      <div className="list">
        {posts.map((item) => {
          const analysis = getAnalysis(item);
          return (
            <a className="list-item" href={item.original_url} key={item.id} target="_blank" rel="noreferrer">
              <div className="list-meta">
                {item.board_name} · 조회 {item.view_count ?? 0} · 추천 {item.upvotes ?? 0} · 댓글 {item.comment_count ?? 0}
              </div>
              <div className="list-headline">
                <strong>{item.title}</strong>
                <span className={`hate-pill hate-pill-${getHateTone(analysis.hate_index)}`}>
                  혐오 지수 {analysis.hate_index.toFixed(1)}
                </span>
              </div>
              <p>{item.body}</p>
              <div className="inline-analysis">
                <span>{getBiasLabel(analysis.market_bias)}</span>
                <span>혐오 {analysis.hate_score.toFixed(1)}</span>
                <span>불확실성 {analysis.uncertainty_score.toFixed(1)}</span>
                <span>태그 {analysis.tags.join(", ") || "없음"}</span>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

function MetricBar({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="metric-bar">
      <div className="metric-bar-head">
        <span>{label}</span>
        <strong>{value.toFixed(1)}%</strong>
      </div>
      <div className="metric-bar-track">
        <div className={`metric-bar-fill metric-bar-fill-${tone}`} style={{ width: `${Math.max(4, value)}%` }} />
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
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function getHateTone(value: number) {
  if (value >= 60) {
    return "high";
  }
  if (value >= 25) {
    return "mid";
  }
  return "low";
}

function getUncertaintyTone(value: number) {
  if (value >= 50) {
    return "high";
  }
  if (value >= 20) {
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
    return "탐욕 우세";
  }
  if (value === "bearish") {
    return "공포 우세";
  }
  return "중립";
}

function getAnalysis(post: CommunityPost) {
  return {
    sentiment_score: 0,
    fear_greed_score: 50,
    hate_score: 0,
    hate_index: 0,
    uncertainty_score: 0,
    market_bias: "neutral",
    keywords: [],
    tags: [],
    topics: [],
    entities: [],
    ...post.analysis,
  };
}
