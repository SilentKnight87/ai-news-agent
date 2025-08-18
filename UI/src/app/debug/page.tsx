"use client"

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function DebugPage() {
  const [status, setStatus] = useState<{
    envVars: boolean
    connection: boolean
    articles: number
    error?: string
  }>({
    envVars: false,
    connection: false,
    articles: 0
  })

  useEffect(() => {
    async function checkStatus() {
      try {
        // Check environment variables
        const hasEnvVars = !!(
          process.env.NEXT_PUBLIC_SUPABASE_URL && 
          process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
        )
        
        setStatus(prev => ({ ...prev, envVars: hasEnvVars }))

        if (!hasEnvVars) {
          setStatus(prev => ({ 
            ...prev, 
            error: 'Missing environment variables: NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY' 
          }))
          return
        }

        // Test connection
        const { data, error } = await supabase
          .from('articles')
          .select('id', { count: 'exact', head: true })

        if (error) {
          setStatus(prev => ({ 
            ...prev, 
            error: `Supabase error: ${error.message}` 
          }))
          return
        }

        const count = data?.length || 0
        setStatus(prev => ({ 
          ...prev, 
          connection: true, 
          articles: count 
        }))

      } catch (err) {
        setStatus(prev => ({ 
          ...prev, 
          error: `Connection error: ${err instanceof Error ? err.message : 'Unknown error'}` 
        }))
      }
    }

    checkStatus()
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-8">AI News Aggregator - Debug Status</h1>
        
        <div className="space-y-4">
          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Environment Variables</h2>
            <div className={`px-3 py-1 rounded text-sm ${status.envVars ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
              {status.envVars ? '✅ Environment variables found' : '❌ Missing environment variables'}
            </div>
            <div className="mt-2 text-sm text-gray-400">
              <div>NEXT_PUBLIC_SUPABASE_URL: {process.env.NEXT_PUBLIC_SUPABASE_URL ? 'Set' : 'Missing'}</div>
              <div>NEXT_PUBLIC_SUPABASE_ANON_KEY: {process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing'}</div>
            </div>
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Database Connection</h2>
            <div className={`px-3 py-1 rounded text-sm ${status.connection ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`}>
              {status.connection ? '✅ Connected to Supabase' : '❌ Connection failed'}
            </div>
          </div>

          <div className="bg-gray-800 p-4 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Data Status</h2>
            <div className="text-sm text-gray-300">
              Articles in database: {status.articles}
            </div>
          </div>

          {status.error && (
            <div className="bg-red-900 p-4 rounded-lg">
              <h2 className="text-lg font-semibold mb-2 text-red-200">Error</h2>
              <pre className="text-sm text-red-300 whitespace-pre-wrap">{status.error}</pre>
            </div>
          )}
        </div>

        <div className="mt-8 bg-gray-800 p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Instructions</h2>
          <div className="text-sm text-gray-300 space-y-2">
            <p>If environment variables are missing, add them to Vercel:</p>
            <ol className="list-decimal list-inside space-y-1 ml-4">
              <li>Go to https://vercel.com/dashboard</li>
              <li>Find your project and go to Settings → Environment Variables</li>
              <li>Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY</li>
              <li>Redeploy the application</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}