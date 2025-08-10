"use client";

import { useMemo } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  totalPages: number;
  onChange: (page: number) => void;
  className?: string;
  showSummary?: boolean;
}

export default function Pagination({
  page,
  totalPages,
  onChange,
  className,
  showSummary = true,
}: PaginationProps) {
  const canPrev = page > 1;
  const canNext = page < totalPages;

  const pages = useMemo(() => {
    // simple windowed page list: first, last, current +/- 1
    const set = new Set<number>([1, totalPages, page - 1, page, page + 1].filter((p) => p >= 1 && p <= totalPages));
    return Array.from(set).sort((a, b) => a - b);
  }, [page, totalPages]);

  const go = (p: number) => {
    if (p < 1 || p > totalPages || p === page) return;
    onChange(p);
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className={cn("flex items-center justify-between gap-3", className)}>
      {showSummary ? (
        <div className="text-sm text-gray-400">Page {page} of {totalPages}</div>
      ) : <div />}

      <div className="flex items-center gap-2">
        <button
          onClick={() => go(page - 1)}
          disabled={!canPrev}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-800 text-gray-300 hover:bg-gray-800/50 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
          Prev
        </button>

        <div className="flex items-center gap-1">
          {pages.map((p, i) => {
            const prev = pages[i - 1];
            const needEllipsis = prev !== undefined && p - prev > 1;
            return (
              <div key={`${p}-${i}`} className="flex items-center gap-1">
                {needEllipsis && <span className="px-1 text-gray-500">…</span>}
                <button
                  onClick={() => go(p)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg border",
                    p === page
                      ? "border-white text-white"
                      : "border-gray-800 text-gray-300 hover:bg-gray-800/50"
                  )}
                  aria-current={p === page ? "page" : undefined}
                >
                  {p}
                </button>
              </div>
            );
          })}
        </div>

        <button
          onClick={() => go(page + 1)}
          disabled={!canNext}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-800 text-gray-300 hover:bg-gray-800/50 disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}