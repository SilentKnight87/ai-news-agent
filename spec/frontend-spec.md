# Frontend Specification - Next.js Dashboard

## Overview
This document specifies the Next.js frontend for the AI News Aggregator, providing real-time article viewing, search capabilities, and daily digest access.

## Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query + Supabase Realtime
- **Deployment**: Vercel

---

## Core Components

### 1. Layout Structure

```typescript
// app/layout.tsx
interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <Header />
        <main className="container mx-auto px-4 py-8">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  )
}
```

### 2. Article Feed Component

```typescript
// components/ArticleFeed.tsx
interface Article {
  id: string
  title: string
  summary: string
  source: 'arxiv' | 'hackernews' | 'rss'
  relevanceScore: number
  publishedAt: Date
  url: string
  keyPoints: string[]
  isDuplicate: boolean
}

export function ArticleFeed() {
  const [filter, setFilter] = useState<FilterOptions>({
    sources: [],
    minRelevance: 0,
    dateRange: 'today'
  })
  
  const { data, isLoading, hasNextPage, fetchNextPage } = useInfiniteQuery({
    queryKey: ['articles', filter],
    queryFn: ({ pageParam = 0 }) => fetchArticles({ ...filter, page: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextPage
  })
  
  return (
    <div className="space-y-4">
      <FilterBar onFilterChange={setFilter} />
      <div className="grid gap-4">
        {data?.pages.map(page => 
          page.articles.map(article => (
            <ArticleCard key={article.id} article={article} />
          ))
        )}
      </div>
      <InfiniteScrollTrigger 
        hasMore={hasNextPage} 
        onLoadMore={fetchNextPage}
      />
    </div>
  )
}
```

### 3. Article Card Design

```typescript
// components/ArticleCard.tsx
export function ArticleCard({ article }: { article: Article }) {
  const sourceColors = {
    arxiv: 'bg-purple-100 text-purple-800',
    hackernews: 'bg-orange-100 text-orange-800',
    rss: 'bg-blue-100 text-blue-800'
  }
  
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold line-clamp-2">
              {article.title}
            </h3>
            <div className="flex items-center gap-2 mt-2">
              <Badge className={sourceColors[article.source]}>
                {article.source}
              </Badge>
              <RelevanceScore score={article.relevanceScore} />
              <TimeAgo date={article.publishedAt} />
            </div>
          </div>
          {article.isDuplicate && (
            <Badge variant="outline">Duplicate</Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-gray-600 line-clamp-3">
          {article.summary}
        </p>
        
        {article.keyPoints.length > 0 && (
          <ul className="mt-3 space-y-1">
            {article.keyPoints.slice(0, 3).map((point, idx) => (
              <li key={idx} className="text-sm text-gray-500 flex items-start">
                <span className="mr-2">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
      
      <CardFooter>
        <Button variant="ghost" size="sm" asChild>
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            Read Original <ExternalLink className="ml-2 h-4 w-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  )
}
```

### 4. Real-time Updates

```typescript
// hooks/useRealtimeArticles.ts
export function useRealtimeArticles() {
  const queryClient = useQueryClient()
  const supabase = createClientComponentClient()
  
  useEffect(() => {
    const channel = supabase
      .channel('articles')
      .on('postgres_changes', 
        { 
          event: 'INSERT', 
          schema: 'public', 
          table: 'articles' 
        },
        (payload) => {
          // Optimistically update the cache
          queryClient.setQueryData(['articles'], (old: any) => {
            return {
              ...old,
              pages: [
                {
                  articles: [payload.new, ...old.pages[0].articles],
                  nextPage: old.pages[0].nextPage
                },
                ...old.pages.slice(1)
              ]
            }
          })
          
          // Show notification
          toast({
            title: "New Article",
            description: payload.new.title,
          })
        }
      )
      .subscribe()
    
    return () => {
      supabase.removeChannel(channel)
    }
  }, [queryClient, supabase])
}
```

---

## Pages Structure

### 1. Home Page (/)
- Latest articles feed
- Quick stats (articles today, top sources)
- Today's digest preview
- Search bar

### 2. Digest Archive (/digest)
- Calendar view of available digests
- Monthly navigation
- Download options (text, audio)

### 3. Article Detail (/article/[id])
- Full article view
- Related articles
- Share options
- Save to collection (future)

### 4. Settings (/settings)
- Notification preferences
- Source selection
- Digest time preference
- Theme toggle

---

## Mobile Responsiveness

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Mobile-Specific Features
- Swipe gestures for article cards
- Bottom sheet for filters
- Simplified navigation
- Touch-optimized controls

---

## Performance Optimizations

### 1. Image Optimization
```typescript
// Use Next.js Image for article thumbnails
<Image
  src={article.thumbnail}
  alt={article.title}
  width={300}
  height={200}
  placeholder="blur"
  blurDataURL={article.thumbnailBlur}
/>
```

### 2. Code Splitting
```typescript
// Lazy load heavy components
const AudioPlayer = dynamic(() => import('./AudioPlayer'), {
  loading: () => <AudioPlayerSkeleton />
})

const SearchDialog = dynamic(() => import('./SearchDialog'), {
  ssr: false
})
```

### 3. Prefetching
```typescript
// Prefetch next page on hover
<Link 
  href={`/article/${article.id}`}
  prefetch={true}
  onMouseEnter={() => prefetchArticle(article.id)}
>
  {article.title}
</Link>
```

---

## Deployment Configuration

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=
```

### Vercel Configuration
```json
{
  "functions": {
    "app/api/*": {
      "maxDuration": 10
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options", 
          "value": "DENY"
        }
      ]
    }
  ]
}
```