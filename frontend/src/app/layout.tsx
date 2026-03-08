import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClawLoom - AI世界模拟器",
  description: "播种角色，编织世界，观察演化，导出故事",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
