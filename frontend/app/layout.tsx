import "./globals.css";

import type { Metadata } from "next";


export const metadata: Metadata = {
  title: "마켓 시그널 허브",
  description: "한국어 경제·정치 커뮤니티 여론 대시보드",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
