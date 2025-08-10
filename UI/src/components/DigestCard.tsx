"use client";

import { DigestSummary } from "@/types";
import { format } from "date-fns";
import { Headphones, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface DigestCardProps {
  digest: DigestSummary;
  onPlayAudio?: (url: string) => void;
  className?: string;
}

export default function DigestCard({ digest, onPlayAudio, className }: DigestCardProps) {
  const dateLabel = digest.date ? format(new Date(digest.date), "PPP") : "";

  return (
    <article
      className={cn(
        "group rounded-xl border border-gray-800/60 bg-gray-900/40 p-5 hover:border-gray-700 transition-colors",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-xs text-gray-400">{dateLabel}</div>
          <h3 className="mt-1 text-lg font-semibold text-white line-clamp-2">{digest.title}</h3>
        </div>
        {digest.audio_url && (
          <button
            onClick={() => onPlayAudio?.(digest.audio_url!)}
            className="shrink-0 inline-flex items-center gap-2 rounded-lg bg-white px-3 py-1.5 text-sm font-medium text-black hover:bg-gray-200 transition-colors"
            aria-label="Play digest audio"
          >
            <Headphones className="h-4 w-4" />
            Listen
          </button>
        )}
      </div>

      <p className="mt-3 text-sm text-gray-300 line-clamp-3">{digest.summary}</p>

      {digest.key_developments?.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {digest.key_developments.slice(0, 3).map((k, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
              <span className="text-green-400">•</span>
              <span className="line-clamp-2">{k}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex items-center gap-3 text-xs text-gray-500">
        <span className="inline-flex items-center gap-1.5">
          <FileText className="h-3.5 w-3.5" />
          {digest.article_count} articles
        </span>
        {typeof digest.audio_duration === "number" && (
          <span className="inline-flex items-center gap-1.5">
            <Headphones className="h-3.5 w-3.5" />
            {Math.round(digest.audio_duration / 60)} min
          </span>
        )}
      </div>
    </article>
  );
}