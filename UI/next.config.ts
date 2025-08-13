import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "static.arxiv.org" },
      { protocol: "https", hostname: "cdn.arstechnica.net" },
      { protocol: "https", hostname: "raw.githubusercontent.com" },
      { protocol: "https", hostname: "user-images.githubusercontent.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
      // Remove wildcard patterns
    ],
  },
};

export default nextConfig;
