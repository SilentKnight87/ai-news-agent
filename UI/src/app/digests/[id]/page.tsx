"use client";

import useSWR from "swr";
import { useParams } from "next/navigation";
import { AudioPlayer } from "@/components/AudioPlayer";
import ArticleCard from "@/components/ArticleCard";
import { Article, DigestSummary } from "@/types";

interface DigestDetail extends DigestSummary {
  articles: Article[];
}

export default function DigestDetailPage() {
  const params = useParams();
  const id = params?.id as string | undefined;

  const { data, isLoading, error } = useSWR<DigestDetail>(id ? `/digests/${id}` : null);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-6 w-40 bg-gray-800 rounded mb-4" />
        <div className="h-4 w-72 bg-gray-800 rounded mb-2" />
        <div className="h-4 w-56 bg-gray-800 rounded mb-6" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="w-80 h-[420px] bg-gray-900 rounded-xl border border-gray-800" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-gray-400">
        Failed to load digest.
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{data.title}</h1>
        <p className="text-gray-400 mt-2">{data.summary}</p>
      </div>

      {data.audio_url && (
        <div className="mb-8">
          <AudioPlayer
            audioUrl={data.audio_url}
            title={data.title}
            duration={data.audio_duration}
            variant="full"
          />
        </div>
      )}

      <section>
        <h2 className="text-xl font-semibold text-white mb-4">Articles ({data.article_count})</h2>
        <div className="flex flex-wrap gap-4">
          {data.articles?.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onClick={() => {
                // no-op: modal handled on home; on detail page we link out
                window.open(article.url, "_blank", "noopener,noreferrer");
              }}
              isVideo={article.source?.toLowerCase() === "youtube"}
            />
          ))}
        </div>
      </section>
    </div>
  );
}