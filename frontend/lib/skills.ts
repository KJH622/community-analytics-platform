import { execFile } from "node:child_process";
import { mkdir, readFile } from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const ROOT = process.cwd();
const FRONTEND_ROOT = path.basename(ROOT).toLowerCase() === "frontend" ? ROOT : path.join(ROOT, "frontend");
const SKILL_ROOT = "C:\\Users\\kjh\\.codex\\skills";

export type SkillKospiQuote = {
  symbol: string;
  source: string;
  index_value: string;
  change_value: string;
  change_percent: string;
  change_direction: string;
  open_value: string;
  high_value: string;
  low_value: string;
  accumulated_volume: number;
  accumulated_value_million_krw: number;
  market_state: string;
  as_of_kst: string;
};

export type SkillNasdaqRow = {
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  diff: number;
  rate: number;
  volume: number;
};

export type SkillKospiHistoryRow = {
  date: string;
  close: number;
  diff: number;
  rate: number;
  volume: number;
  trade_value: number;
};

export type ScrapedCommunityPost = {
  rank: string;
  title: string;
  community: string;
  board: string;
  date: string;
  summary: string;
  stats: string;
  signal: string;
  post_url: string;
};

export async function fetchKospiFromSkill(): Promise<SkillKospiQuote | null> {
  try {
    const { stdout } = await execFileAsync("python", [
      path.join(SKILL_ROOT, "naver-kospi-fetch", "scripts", "fetch_kospi.py"),
    ]);
    return JSON.parse(stdout) as SkillKospiQuote;
  } catch {
    return null;
  }
}

export async function fetchNasdaqFromSkill(days = 3): Promise<SkillNasdaqRow[]> {
  try {
    const { stdout } = await execFileAsync("python", [
      path.join(SKILL_ROOT, "naver-nasdaq-index", "scripts", "fetch_nasdaq.py"),
      "--days",
      String(days),
      "--json",
    ]);
    return JSON.parse(stdout) as SkillNasdaqRow[];
  } catch {
    return [];
  }
}

export async function fetchKospiHistoryFromSkill(days = 7): Promise<SkillKospiHistoryRow[]> {
  try {
    const { stdout } = await execFileAsync("python", [
      path.join(FRONTEND_ROOT, "scripts", "fetch_kospi_history.py"),
      String(days),
    ]);
    return JSON.parse(stdout) as SkillKospiHistoryRow[];
  } catch {
    return [];
  }
}

export async function fetchCommunityPostsFromSkill(): Promise<ScrapedCommunityPost[]> {
  const cacheDir = path.join(ROOT, ".cache");
  const outputPath = path.join(cacheDir, "community-posts.json");
  const configPath = path.join(ROOT, "data", "community-scraper-config.json");

  try {
    await mkdir(cacheDir, { recursive: true });
    await execFileAsync("python", [
      path.join(SKILL_ROOT, "community-post-scraper", "scripts", "scrape_posts.py"),
      "--config",
      configPath,
      "--output",
      outputPath,
    ]);
    const raw = await readFile(outputPath, "utf-8");
    return JSON.parse(raw) as ScrapedCommunityPost[];
  } catch {
    return [];
  }
}
