import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/database'

function getSupabaseConfig() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase environment variables. Please check NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.')
  }

  return { supabaseUrl, supabaseAnonKey }
}

// Defer environment variable check until first access
let _supabase: ReturnType<typeof createClient<Database>> | null = null

function getSupabaseClient() {
  if (!_supabase) {
    // Only check environment variables when client is first accessed
    if (typeof window === 'undefined') {
      // Server-side: Skip initialization in SSR/build environments
      return null
    }
    
    const { supabaseUrl, supabaseAnonKey } = getSupabaseConfig()
    
    _supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: false, // Anonymous access only
      },
      db: {
        schema: 'public',
      },
      global: {
        headers: {
          'x-application-name': 'ai-news-frontend',
        },
      },
    })
  }
  
  return _supabase
}

export const supabase = new Proxy({} as ReturnType<typeof createClient<Database>>, {
  get(target, prop) {
    const client = getSupabaseClient()
    if (!client) {
      throw new Error('Supabase client not available in SSR context')
    }
    return client[prop as keyof typeof client]
  }
})

export type SupabaseClient = typeof supabase