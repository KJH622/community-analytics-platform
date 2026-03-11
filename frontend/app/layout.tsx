import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Market Signal Hub",
  description: "경제 데이터, 뉴스, 커뮤니티 감정, 정치 반응을 함께 보는 통합 대시보드",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <div className="shell">
          <header className="topbar">
            <div className="topbar-copy">
              <span className="brand-kicker">REALTIME INTELLIGENCE</span>
              <div className="brand-title">Market Signal Hub</div>
              <div className="brand-subtitle">
                경제 데이터, 뉴스, 커뮤니티 반응과 정치 흐름을 한 화면에서 읽는 실시간 시그널 대시보드
              </div>
            </div>

            <nav className="nav">
              <Link href="/">Dashboard</Link>
              <Link href="/politics">Politics</Link>
              <Link href="/news">News</Link>
              <Link href="/community">Community</Link>
            </nav>
          </header>

          {children}
        </div>
      </body>
    </html>
  );
}
