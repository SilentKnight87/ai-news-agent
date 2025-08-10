"use client";

import { useState } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { useDebounce } from "@/hooks/useDebounce";
import { useSearch } from "@/hooks/useSearch";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

type SourceOption = { id: string; label: string };

interface SearchBarProps {
  onClose?: () => void;
  className?: string;
  sourceOptions?: SourceOption[];
}

const DEFAULT_SOURCES: SourceOption[] = [
  { id: "all", label: "All" },
  { id: "arxiv", label: "ArXiv" },
  { id: "hackernews", label: "Hacker News" },
  { id: "rss", label: "RSS" },
  { id: "youtube", label: "YouTube" },
  { id: "huggingface", label: "HuggingFace" },
  { id: "reddit", label: "Reddit" },
  { id: "github", label: "GitHub" },
];

export default function SearchBar({ onClose, className, sourceOptions = DEFAULT_SOURCES }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState<string>("all");
  const debouncedQuery = useDebounce(query, 300);

  const effectiveSource = source === "all" ? undefined : source;
  const { data, isLoading } = useSearch(debouncedQuery, effectiveSource);

  return (
    <div className={cn("relative w-[320px]", className)}>
      <div className="relative">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search articles..."
              className="w-full h-10 pl-10 pr-8 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-500 focus:bg-gray-900 transition-all"
              autoFocus
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Close search"
              >
                <X className="w-3.5 h-3.5 text-gray-400" />
              </button>
            )}
          </div>

          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="bg-gray-900/80 border border-gray-700 rounded-lg text-xs px-2 py-1.5 text-gray-300 focus:outline-none focus:border-gray-500"
            aria-label="Filter by source"
            title="Filter by source"
          >
            {sourceOptions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Suggestions dropdown */}
      {(isLoading || (data?.articles?.length ?? 0) > 0) && query.trim().length > 0 && (
        <div className="absolute z-50 mt-2 w-full bg-gray-900 border border-gray-800 rounded-xl shadow-xl overflow-hidden">
          {isLoading && (
            <div className="px-4 py-3 flex items-center gap-2 text-gray-400 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Searching...
            </div>
          )}
          {!isLoading && (data?.articles?.length ?? 0) === 0 && (
            <div className="px-4 py-3 text-gray-500 text-sm">No results</div>
          )}
          {!isLoading && (data?.articles?.length ?? 0) > 0 && (
            <ul className="max-h-80 overflow-y-auto divide-y divide-gray-800">
              {data!.articles.slice(0, 8).map((a) => (
                <li key={a.id}>
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block px-4 py-3 hover:bg-gray-800 transition-colors"
                  >
                    <div className="text-xs text-gray-400 mb-1">
                      {a.source} • {formatDistanceToNow(new Date(a.published_at), { addSuffix: true })}
                    </div>
                    <div className="text-sm text-gray-100 line-clamp-2">{a.title}</div>
                  </a>
                </li>
              ))}
              {data!.total > 8 && (
                <li className="px-4 py-2 text-xs text-gray-500">Showing 8 of {data!.total} results</li>
              )}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}