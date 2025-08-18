"use client";

import { SWRConfig } from "swr";
import { ReactNode } from "react";
import { Toaster, toast } from "react-hot-toast";
import { useErrorDisplay } from "@/hooks/useSupabaseError";
import { PostgrestError } from '@supabase/supabase-js';

interface ClientProvidersProps {
  children: ReactNode;
}

export default function ClientProviders({ children }: ClientProvidersProps) {
  const { getDisplayMessage, shouldShowRetry } = useErrorDisplay();

  return (
    <>
      <SWRConfig
        value={{
          revalidateOnFocus: false,
          revalidateOnReconnect: true,
          dedupingInterval: 60000,
          errorRetryCount: 3,
          errorRetryInterval: 5000,
          // Global error handling for Supabase errors
          onError: (err: unknown) => {
            // Handle PostgrestError (Supabase database errors)
            if (typeof err === 'object' && err !== null && 'code' in err) {
              const postgrestError = err as PostgrestError;
              
              // Don't show toasts for expected "no data" scenarios
              if (postgrestError.code === 'PGRST204') return;
              
              // Show user-friendly error messages
              const message = getDisplayMessage(err);
              toast.error(message);
              return;
            }

            // Handle network/connection errors
            if (err instanceof Error) {
              if (err.message.includes('fetch') || err.message.includes('network')) {
                toast.error("Connection failed. Please check your internet connection.");
                return;
              }
              
              // Generic error handling
              console.error('SWR Error:', err);
              toast.error(getDisplayMessage(err));
              return;
            }

            // Unknown error type
            console.error('Unknown SWR error:', err);
            toast.error("An unexpected error occurred");
          },
          shouldRetryOnError: (err: unknown) => {
            // Use our error handling logic to determine if we should retry
            return shouldShowRetry(err);
          },
        }}
      >
        {children}
      </SWRConfig>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { 
            background: "#111827", 
            color: "#fff", 
            border: "1px solid #1f2937"
          },
          duration: 4000,
        }}
      />
    </>
  );
}