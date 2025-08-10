"use client";

import { useState } from "react";
import useSWR from "swr";
import DigestCard from "@/components/DigestCard";
import Pagination from "@/components/Pagination";
import { AudioPlayer } from "@/components/AudioPlayer";
import { DigestSummary, PaginationMeta } from "@/types";

export default function DigestsPage() {
  const [page, setPage] = useState(1);
  const perPage = 10;

  const { data } = useSWR<{ digests: DigestSummary[]; pagination: PaginationMeta }>(
    `/digests?page=${page}&per_page=${perPage}`
  );

  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold mb-6">AI Digests</h1>

      <div className="grid gap-4">
        {data?.digests?.map((digest) => (
          <DigestCard
            key={digest.id}
            digest={digest}
            onPlayAudio={(url) => setAudioUrl(url)}
          />
        ))}
      </div>

      <div className="mt-8">
        <Pagination
          page={data?.pagination?.page ?? page}
          totalPages={data?.pagination?.total_pages ?? 1}
          onChange={setPage}
        />
      </div>

      {audioUrl && (
        <AudioPlayer
          audioUrl={audioUrl}
          title="AI News Digest"
          variant="full"
          onClose={() => setAudioUrl(null)}
        />
      )}
    </div>
  );
}