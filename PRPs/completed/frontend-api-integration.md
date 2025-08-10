# Frontend API Integration Specification

## Overview
This specification details the integration requirements for connecting the Next.js frontend to the newly implemented backend APIs. The frontend needs to leverage these APIs to provide search, filtering, pagination, and content discovery features.

## Current State
- **Backend**: 6 core API endpoints fully implemented and tested
- **Frontend**: Basic UI components exist but not connected to new APIs
- **Gap**: Frontend is using mock data or limited endpoints

## API Endpoints to Integrate

### 1. Search API
**Endpoint**: `GET /api/v1/articles/search`
**Parameters**:
- `q`: Search query (required)
- `source`: Optional source filter
- `limit`: Results per page (1-100)
- `offset`: Pagination offset

**Frontend Requirements**:
- Search bar component in header
- Real-time search suggestions (debounced)
- Search results page with highlighting
- Source filter dropdown in search UI
- Load more functionality

**Implementation**:
```typescript
// hooks/useSearch.ts
const useSearch = (query: string, source?: ArticleSource) => {
  return useSWR(
    query ? `/api/v1/articles/search?q=${query}&source=${source}` : null,
    fetcher,
    { 
      revalidateOnFocus: false,
      dedupingInterval: 1000 
    }
  );
};
```

### 2. Filter API
**Endpoint**: `GET /api/v1/articles/filter`
**Parameters**:
- `start_date`: Filter after date
- `end_date`: Filter before date
- `relevance_min`: Minimum relevance (0-100)
- `relevance_max`: Maximum relevance (0-100)
- `sources`: Comma-separated sources
- `categories`: Comma-separated categories

**Frontend Requirements**:
- FilterBar component updates
- Date range picker
- Relevance score slider (fix current spacing issues)
- Multi-select for sources
- Category tag selector
- Clear filters button
- Filter count badge

**Implementation**:
```typescript
// components/FilterBar.tsx updates
interface FilterState {
  dateRange: [Date | null, Date | null];
  relevanceRange: [number, number];
  sources: ArticleSource[];
  categories: string[];
}

const applyFilters = async (filters: FilterState) => {
  const params = new URLSearchParams();
  if (filters.dateRange[0]) params.append('start_date', filters.dateRange[0].toISOString());
  if (filters.dateRange[1]) params.append('end_date', filters.dateRange[1].toISOString());
  // ... build params
  
  const response = await fetch(`/api/v1/articles/filter?${params}`);
  return response.json();
};
```

### 3. Enhanced Pagination
**Endpoint**: `GET /api/v1/articles`
**Parameters**:
- `page`: Page number (1-indexed)
- `per_page`: Items per page
- `sort_by`: Field to sort by
- `order`: asc/desc
- `source`: Optional source filter

**Frontend Requirements**:
- Replace infinite scroll with page-based navigation
- Page number display (e.g., "Page 3 of 10")
- Previous/Next buttons
- Jump to page input
- Items per page selector
- Sort dropdown (date, relevance, title)

**Implementation**:
```typescript
// hooks/usePaginatedArticles.ts
interface PaginationState {
  page: number;
  perPage: number;
  sortBy: string;
  order: 'asc' | 'desc';
}

const usePaginatedArticles = (pagination: PaginationState) => {
  const { data, error } = useSWR(
    `/api/v1/articles?page=${pagination.page}&per_page=${pagination.perPage}`,
    fetcher
  );
  
  return {
    articles: data?.articles || [],
    pagination: data?.pagination,
    meta: data?.meta,
    isLoading: !error && !data,
    error
  };
};
```

### 4. Digests List
**Endpoint**: `GET /api/v1/digests`
**Parameters**:
- `page`: Page number
- `per_page`: Digests per page

**Frontend Requirements**:
- New Digests page/route
- Digest card component
- Audio player integration
- Key developments display
- Article count badge
- Date formatting

**Implementation**:
```typescript
// pages/digests.tsx
export default function DigestsPage() {
  const [page, setPage] = useState(1);
  const { data } = useSWR(`/api/v1/digests?page=${page}`, fetcher);
  
  return (
    <div>
      {data?.digests.map(digest => (
        <DigestCard 
          key={digest.id}
          digest={digest}
          onPlayAudio={() => playAudio(digest.audio_url)}
        />
      ))}
      <Pagination 
        current={page}
        total={data?.pagination.total_pages}
        onChange={setPage}
      />
    </div>
  );
}
```

### 5. Single Digest Detail
**Endpoint**: `GET /api/v1/digests/{id}`

**Frontend Requirements**:
- Digest detail page
- Full article list display
- Audio player with controls
- Share functionality
- Related articles section

### 6. Sources Metadata
**Endpoint**: `GET /api/v1/sources`

**Frontend Requirements**:
- Sources overview page
- Source statistics cards
- Last fetch time display
- Article count per source
- Average relevance scores
- Source status indicators

## Data Models to Update

```typescript
// types/index.ts additions

export interface SearchResponse {
  articles: Article[];
  total: number;
  query: string;
  took_ms: number;
}

export interface FilterResponse {
  articles: Article[];
  filters_applied: Record<string, any>;
  total: number;
  took_ms: number;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface DigestSummary {
  id: string;
  date: string;
  title: string;
  summary: string;
  key_developments: string[];
  article_count: number;
  audio_url?: string;
  audio_duration?: number;
}

export interface SourceMetadata {
  name: string;
  display_name: string;
  description: string;
  article_count: number;
  last_fetch?: string;
  last_published?: string;
  avg_relevance_score: number;
  status: 'active' | 'inactive';
  icon_url: string;
}
```

## UI Component Updates

### 1. SearchBar Component
```typescript
// components/SearchBar.tsx
const SearchBar = () => {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const { data, isLoading } = useSearch(debouncedQuery);
  
  return (
    <div className="relative">
      <input 
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search articles..."
        className="w-full px-4 py-2 rounded-lg"
      />
      {isLoading && <Spinner />}
      {data && <SearchResults results={data.articles} />}
    </div>
  );
};
```

### 2. FilterBar Fixes
- Fix relevance slider spacing issue
- Add date picker component
- Implement multi-select dropdowns
- Add active filter count badge
- Clear all filters button

### 3. ArticleCard Updates
- Remove placeholder images
- Implement actual image URLs from sources
- Clean LaTeX formatting in content
- Fix alignment issues
- Add relevance score display

### 4. ArticleModal Cleanup
- Remove non-functional buttons (share, bookmark, reanalyze)
- Fix LaTeX symbol rendering
- Implement related articles if data available
- Add source metadata display

## API Integration Strategy

### Phase 1: Core Integration (2 days)
1. Update data fetching hooks
2. Replace mock data with API calls
3. Implement error handling
4. Add loading states

### Phase 2: Search & Filter (1 day)
1. Implement search functionality
2. Fix and connect FilterBar
3. Add filter persistence in URL
4. Implement filter combinations

### Phase 3: Pagination (1 day)
1. Replace infinite scroll
2. Add pagination controls
3. Implement sort functionality
4. Add per-page selector

### Phase 4: Digests (1 day)
1. Create digests page
2. Implement digest cards
3. Connect audio player
4. Add digest detail view

### Phase 5: Polish (1 day)
1. Fix LaTeX rendering
2. Implement image handling
3. Clean up modal
4. Add source statistics page

## Performance Considerations

### Caching Strategy
```typescript
// lib/fetcher.ts
const fetcher = async (url: string) => {
  const res = await fetch(url, {
    headers: {
      'Cache-Control': 'max-age=60', // 1 minute cache
    }
  });
  
  if (!res.ok) {
    throw new Error('Failed to fetch');
  }
  
  return res.json();
};

// Use SWR's built-in caching
const swrConfig = {
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  dedupingInterval: 60000, // 1 minute
};
```

### Optimistic Updates
```typescript
// For filters and pagination
const optimisticUpdate = (key: string, data: any) => {
  mutate(key, data, false);
  // Then revalidate
  mutate(key);
};
```

## Error Handling

### Global Error Boundary
```typescript
// components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback />;
    }
    
    return this.props.children;
  }
}
```

### API Error Handler
```typescript
// lib/apiClient.ts
class APIError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

const handleAPIError = (error: APIError) => {
  switch (error.status) {
    case 404:
      toast.error('Content not found');
      break;
    case 500:
      toast.error('Server error. Please try again.');
      break;
    default:
      toast.error('Something went wrong');
  }
};
```

## Testing Requirements

### Unit Tests
- Test each hook with mock data
- Test filter state management
- Test pagination logic
- Test search debouncing

### Integration Tests
- Test API calls with MSW
- Test error scenarios
- Test loading states
- Test empty states

### E2E Tests
- Search flow
- Filter application
- Pagination navigation
- Digest viewing

## Success Metrics

### Performance
- Search response < 500ms
- Filter application < 300ms
- Page navigation < 200ms
- Initial load < 2s

### User Experience
- No placeholder images
- Clean text (no LaTeX symbols)
- Smooth pagination
- Working audio player
- Responsive filters

## Migration Checklist

- [ ] Update environment variables for API URLs
- [ ] Install required dependencies (date-picker, etc.)
- [ ] Update TypeScript types
- [ ] Implement data fetching hooks
- [ ] Update existing components
- [ ] Create new pages (digests, sources)
- [ ] Fix known UI issues
- [ ] Add error handling
- [ ] Implement caching
- [ ] Write tests
- [ ] Performance optimization
- [ ] Deploy and monitor

## Dependencies to Add

```json
{
  "dependencies": {
    "react-datepicker": "^4.25.0",
    "@types/react-datepicker": "^4.19.5",
    "react-select": "^5.8.0",
    "date-fns": "^3.0.0",
    "lodash.debounce": "^4.0.8"
  }
}
```

## Timeline

- **Day 1**: Core API integration, hooks, error handling
- **Day 2**: Search and filter implementation
- **Day 3**: Pagination and sorting
- **Day 4**: Digests and audio integration
- **Day 5**: UI fixes, polish, testing
- **Day 6**: Deployment and monitoring

## Notes

### Critical Fixes Needed
1. **LaTeX Cleanup**: Implement a utility function to strip LaTeX symbols
2. **Image Handling**: Determine source for article images or use smart placeholders
3. **FilterBar Spacing**: Fix overlap issues with relevance slider
4. **Modal Buttons**: Remove or implement share/bookmark functionality

### Future Enhancements
- Real-time updates via WebSocket
- Offline support with service workers
- Advanced search with operators
- Saved searches and filters
- User preferences persistence