"use client";

import useSWR from "swr";
import { SourceMetadata } from "@/types";
import { CheckCircle2, XCircle, Clock3, Newspaper } from "lucide-react";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm text-gray-200">{value}</span>
    </div>
  );
}

function SourceCard({ s }: { s: SourceMetadata }) {
  const statusIcon =
    s.status === "active" ? (
      <CheckCircle2 className="w-4 h-4 text-green-400" />
    ) : (
      <XCircle className="w-4 h-4 text-gray-500" />
    );

  return (
    <article className="rounded-xl border border-gray-800/60 bg-gray-900/40 p-5 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            {s.icon_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={s.icon_url} alt={s.display_name} className="w-5 h-5 rounded-sm" />
            ) : (
              <Newspaper className="w-5 h-5 text-gray-400" />
            )}
            <h3 className="text-base font-semibold text-white">{s.display_name || s.name}</h3>
          </div>
          <p className="mt-2 text-sm text-gray-400 line-clamp-2">{s.description}</p>
        </div>
        <div className="shrink-0 inline-flex items-center gap-2 rounded-lg border border-gray-800 px-2 py-1 text-xs">
          {statusIcon}
          <span className={s.status === "active" ? "text-green-400" : "text-gray-400"}>
            {s.status}
          </span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Articles" value={s.article_count} />
        <Stat label="Avg Relevance" value={`${Math.round(s.avg_relevance_score)}%`} />
        <div className="flex items-center gap-2">
          <Clock3 className="w-4 h-4 text-gray-500" />
          <Stat label="Last Fetch" value={s.last_fetch ? new Date(s.last_fetch).toLocaleString() : "—"} />
        </div>
        <Stat label="Last Published" value={s.last_published ? new Date(s.last_published).toLocaleString() : "—"} />
      </div>
    </article>
  );
}

export default function SourcesPage() {
  const { data, isLoading, error } = useSWR<SourceMetadata[]>("/sources");

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="h-6 w-48 bg-gray-800 rounded mb-6" />
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-36 bg-gray-900 rounded-xl border border-gray-800" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-gray-400">
        Failed to load sources.
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold mb-6">Sources Overview</h1>
      <div className="grid gap-4 md:grid-cols-2">
        {data.map((s) => (
          <SourceCard key={s.name} s={s} />
        ))}
      </div>
    </div>
  );
}