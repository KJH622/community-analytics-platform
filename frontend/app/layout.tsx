import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { Noto_Sans_KR, Space_Grotesk } from "next/font/google";

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

const bodyFont = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Market Signal Hub",
  description: "Economic data, news, community sentiment, and political analytics dashboard",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>
        <div className="shell">
          <header className="topbar">
            <div className="brand">
              <div className="brand-kicker">Realtime Intelligence</div>
              <div className="brand-title">Market Signal Hub</div>
              <div className="brand-subtitle">
                경제 데이터, 뉴스, 커뮤니티 반응을 한 화면에서 읽는 시장 시그널 대시보드
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
