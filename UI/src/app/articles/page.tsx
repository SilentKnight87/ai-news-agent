"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Article, SortField, SortOrder } from "@/types";
import ArticleCard from "@/components/ArticleCard";
import Pagination from "@/components/Pagination";
import { usePaginatedArticles } from "@/hooks/usePaginatedArticles";

function useQueryState() {
  const params = useSearchParams();
  const router = useRouter();

  const page = Number(params.get("page") || 1);
  const perPage = Number(params.get("per_page") || 12);
  const sortBy = (params.get("sort_by") as SortField) || "published_at";
  const order = (params.get("order") as SortOrder) || "desc";
  const source = params.get("source") || undefined;

  const setQuery = (next: Partial<{ page: number; per_page: number; sort_by: SortField; order: SortOrder; source?: string }>) => {
    const sp = new URLSearchParams(params.toString());
    if (next.page !== undefined) sp.set("page", String(next.page));
    if (next.per_page !== undefined) sp.set("per_page", String(next.per_page));
    if (next.sort_by !== undefined) sp.set("sort_by", next.sort_by);
    if (next.order !== undefined) sp.set("order", next.order);
    if (next.source !== undefined) {
      if (next.source) sp.set("source", next.source);
      else sp.delete("source");
    }
    router.push(`/articles?${sp.toString()}`);
  };

  return { page, perPage, sortBy, order, source, setQuery };
}

export default function ArticlesPage() {
  const { page, perPage, sortBy, order, source, setQuery } = useQueryState();

  const { articles, pagination, meta, isLoading, error } = usePaginatedArticles({
    page,
    perPage,
    sortBy,
    order,
    source,
  });

  const totalPages = pagination?.total_pages ?? 1;

  const handleChangePage = (p: number) => setQuery({ page: p });
  const handleChangePerPage = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newPerPage = Number(e.target.value);
    setQuery({ per_page: newPerPage, page: 1 });
  };
  const handleChangeSort = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setQuery({ sort_by: e.target.value as SortField, page: 1 });
  };
  const handleToggleOrder = () => {
    setQuery({ order: order === "asc" ? "desc" : "asc", page: 1 });
  };
  const handleChangeSource = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    setQuery({ source: v === "all" ? "" : v, page: 1 });
  };

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6 gap-3">
        <h1 className="text-2xl font-bold">Articles</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Source</label>
          <select
            value={source || "all"}
            onChange={handleChangeSource}
            className="bg-gray-900/80 border border-gray-700 rounded-lg text-xs px-2 py-1.5 text-gray-300 focus:outline-none focus:border-gray-500"
          >
            <option value="all">All</option>
            <option value="arxiv">ArXiv</option>
            <option value="hackernews">Hacker News</option>
            <option value="rss">RSS</option>
            <option value="youtube">YouTube</option>
            <option value="huggingface">HuggingFace</option>
            <option value="reddit">Reddit</option>
            <option value="github">GitHub</option>
          </select>

          <label className="ml-3 text-sm text-gray-400">Sort</label>
          <select
            value={sortBy}
            onChange={handleChangeSort}
            className="bg-gray-900/80 border border-gray-700 rounded-lg text-xs px-2 py-1.5 text-gray-300 focus:outline-none focus:border-gray-500"
          >
            <option value="published_at">Date</option>
            <option value="relevance_score">Relevance</option>
            <option value="title">Title</option>
            <option value="fetched_at">Fetched</option>
          </select>

          <button
            onClick={handleToggleOrder}
            className="px-2 py-1.5 text-xs rounded-lg border border-gray-700 text-gray-300 hover:bg-gray-800/50"
            aria-label="Toggle order"
            title="Toggle order"
          >
            {order === "asc" ? "Asc" : "Desc"}
          </button>

          <label className="ml-3 text-sm text-gray-400">Per page</label>
          <select
            value={perPage}
            onChange={handleChangePerPage}
            className="bg-gray-900/80 border border-gray-700 rounded-lg text-xs px-2 py-1.5 text-gray-300 focus:outline-none focus:border-gray-500"
          >
            {[6, 12, 18, 24, 36].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: perPage }).map((_, i) => (
            <div key={i} className="w-80 h-[420px] bg-gray-900 rounded-xl border border-gray-800" />
          ))}
        </div>
      ) : null}
 
      {!isLoading && error ? (
        <div className="text-center text-gray-400 py-12">Failed to load articles.</div>
      ) : null}
 
      {!isLoading && !error ? (
        <>
          {articles.length === 0 ? (
            <div className="text-center text-gray-400 py-12">No articles found.</div>
          ) : (
            <>
              <div className="flex flex-wrap gap-4">
                {articles.map((a: Article) => (
                  <ArticleCard
                    key={a.id}
                    article={a}
                    onClick={(article) => window.open(article.url, "_blank", "noopener,noreferrer")}
                    isVideo={a.source?.toLowerCase() === "youtube"}
                  />
                ))}
              </div>
              <div className="mt-8">
                <Pagination page={pagination?.page ?? page} totalPages={totalPages} onChange={handleChangePage} />
              </div>
            </>
          )}
        </>
      ) : null}
    </div>
  );
}