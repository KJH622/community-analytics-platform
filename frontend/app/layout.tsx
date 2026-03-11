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
            <div>
              <div className="brand-title">Market Signal Hub</div>
              <div className="brand-subtitle">
                한국 경제·정치 커뮤니티를 주기적으로 수집하고 감정 분석에 활용하는 통합 대시보드입니다.
              </div>
            </div>
            <nav className="nav">
              <Link href="/">경제</Link>
              <Link href="/politics">정치</Link>
              <Link href="/news">뉴스</Link>
              <Link href="/community">커뮤니티</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
