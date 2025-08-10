"use client";

import { SWRConfig } from "swr";
import { ReactNode } from "react";
import { fetcher, swrConfig, APIError } from "@/lib/fetcher";
import { Toaster, toast } from "react-hot-toast";

interface ClientProvidersProps {
  children: ReactNode;
}

export default function ClientProviders({ children }: ClientProvidersProps) {
  return (
    <>
      <SWRConfig
        value={{
          fetcher,
          ...swrConfig,
          // Don't spam the user with toasts for 404s on optional widgets (stats/digest etc.)
          onError: (err: unknown) => {
            if (err instanceof APIError) {
              if (err.status === 404) return; // silent for not found
              if (err.status === 500) {
                toast.error("Server error. Please try again.");
                return;
              }
              toast.error(err.message || "Something went wrong");
              return;
            }
            // Network or unknown error
            // Keep this low-noise; log to console and show a generic toast once
            // Users will still see component-level fallbacks
            // eslint-disable-next-line no-console
            console.error(err);
            toast.error("Network error");
          },
          shouldRetryOnError: (err: unknown) => {
            if (err instanceof APIError) {
              // Don't retry on client or not-found errors
              if ([401, 403, 404, 422].includes(err.status)) return false;
            }
            return true;
          },
        }}
      >
        {children}
      </SWRConfig>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "#111827", color: "#fff", border: "1px solid #1f2937" },
        }}
      />
    </>
  );
}