import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Header from "@/components/Header";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI News Aggregator - Intelligent News Discovery",
  description: "Stay ahead with AI-curated news from ArXiv, Hacker News, GitHub, and more. Real-time relevance scoring and daily AI digests.",
  keywords: "AI news, machine learning, technology news, ArXiv papers, Hacker News, GitHub trends",
  authors: [{ name: "AI News Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#000000",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="bg-black text-white antialiased">
        <Header />
        <main className="pt-16 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
