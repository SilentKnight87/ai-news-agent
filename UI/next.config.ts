import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "i.ytimg.com" },
      { protocol: "https", hostname: "pbs.twimg.com" },
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "miro.medium.com" },
      { protocol: "https", hostname: "static.arxiv.org" },
      { protocol: "https", hostname: "cdn.arstechnica.net" },
      { protocol: "https", hostname: "**.githubusercontent.com" as any },
      { protocol: "https", hostname: "**.ytimg.com" as any },
    ],
  },
};

export default nextConfig;
