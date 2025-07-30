name: "Netflix-Style Frontend Implementation PRP"
description: |
  
## Purpose
Comprehensive PRP for implementing a Netflix-style content discovery interface with horizontal scrolling card rows for AI/ML news aggregation, including all necessary context for one-pass implementation success.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Build a modern Netflix-style frontend interface for the AI News Aggregator with horizontal scrolling card rows, smooth animations, real-time updates, and responsive design. The interface should provide an immersive content discovery experience with Netflix-inspired visual design patterns.

## Why
- **User Experience**: Netflix-style interfaces are proven to increase user engagement by 40-60% through intuitive content discovery
- **Content Organization**: Horizontal rows allow efficient organization of different data sources (ArXiv, HackerNews, RSS, Daily Digests)
- **Mobile-First**: Touch-optimized interactions are essential for modern web applications
- **Brand Differentiation**: Premium visual design elevates the product above standard news aggregators
- **Performance**: Virtualized scrolling enables handling thousands of articles without performance degradation

## What
A complete Next.js 14+ frontend application with:
- Netflix-style horizontal scrolling card rows for each data source
- Interactive hover animations with AI summary overlays
- Real-time content updates with smooth transitions
- Responsive design optimized for mobile and desktop
- Dark/light theme support with cinematic color schemes
- Audio playback for daily digest summaries
- In-app browser for seamless article reading

### Success Criteria
- [ ] Smooth 60fps animations on all interactions
- [ ] Responsive design working on mobile (320px+) to desktop (1920px+)
- [ ] Horizontal scrolling with momentum physics and touch gestures
- [ ] Real-time data integration with existing Python backend API
- [ ] Accessibility compliance (WCAG 2.1 AA)
- [ ] Core Web Vitals scores: LCP < 2.5s, FID < 100ms, CLS < 0.1

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://nextjs.org/docs/14/app/building-your-application/data-fetching/patterns
  why: Next.js 14 App Router data fetching patterns and SSR integration
  
- url: https://swr.vercel.app/docs/with-nextjs
  why: SWR integration with Next.js App Router for real-time data updates
  
- url: https://www.framer.com/motion/
  why: Framer Motion animation patterns for Netflix-style hover effects
  section: Layout animations, gesture handling, and performance optimization
  critical: Use transform3d and will-change for GPU acceleration
  
- url: https://web.dev/articles/virtualize-long-lists-react-window
  why: React-window virtualization for handling thousands of article cards
  section: Horizontal scrolling implementation with FixedSizeList
  critical: Use overscanCount for smooth scrolling without performance loss

- url: https://tailwindcss.com/docs/responsive-design
  why: Responsive design patterns and mobile-first approach
  
- url: https://headlessui.com/
  why: Accessible UI components for modals, dropdowns, and interactive elements
  
- file: src/api/routes.py
  why: Understanding existing API endpoints for data integration
  
- file: src/models/articles.py
  why: Article model structure and validation patterns to follow
  
- file: src/models/schemas.py
  why: API response schemas and TypeScript type generation
  
- docfile: ai_docs/color-palette.md
  why: Brand color palette for consistent theming
```

### Current Codebase Structure
```bash
ai-news-aggregator-agent/
├── src/                          # Python backend
│   ├── api/
│   │   └── routes.py            # API endpoints: /articles, /digest/latest, /stats
│   ├── models/
│   │   ├── articles.py          # Article, DailyDigest models
│   │   └── schemas.py           # API request/response schemas  
│   └── services/                # Business logic services
└── ai_docs/
    └── color-palette.md         # Brand colors: black-bean, citrine, fulvous, turkey-red, rosewood
```

### Desired Frontend Structure
```bash
frontend/                        # New Next.js 14+ App Router application
├── app/
│   ├── (dashboard)/
│   │   ├── page.tsx            # Main streaming dashboard layout
│   │   └── layout.tsx          # Dashboard layout with navigation
│   ├── globals.css             # Global styles with CSS variables
│   └── layout.tsx              # Root layout with providers
├── components/
│   ├── cards/
│   │   ├── NetflixCard.tsx     # Netflix-style article card with hover expansion
│   │   ├── AudioDigestCard.tsx # Audio card for daily digest playback
│   │   └── CardSkeleton.tsx    # Loading skeleton matching card dimensions
│   ├── rows/
│   │   ├── HorizontalRow.tsx   # Virtualized horizontal scrolling container
│   │   ├── ArticleRow.tsx      # Article-specific row with source filtering
│   │   └── DigestRow.tsx       # Daily digest audio cards row
│   ├── modals/
│   │   ├── ContentModal.tsx    # Full-screen content detail modal
│   │   └── InAppBrowser.tsx    # Iframe-based browser component
│   ├── ui/
│   │   ├── HeroSection.tsx     # Cinematic header with featured content
│   │   └── Navigation.tsx      # Floating navigation overlay
│   └── providers/
│       ├── SWRProvider.tsx     # SWR configuration with fallback data
│       └── ThemeProvider.tsx   # Dark/light theme management
├── hooks/
│   ├── useHoverAnimation.ts    # Netflix-style card hover effects
│   ├── useHorizontalScroll.ts  # Touch-optimized horizontal scrolling
│   ├── useInAppBrowser.ts      # In-app browser functionality
│   └── useRealTimeUpdates.ts   # SWR-based real-time data updates
├── lib/
│   ├── api.ts                  # API client with TypeScript types
│   ├── animations.ts           # Framer Motion animation variants
│   └── utils.ts                # Utility functions and constants
├── styles/
│   ├── netflix-themes.css      # Cinematic dark/light theme variables
│   └── components.css          # Component-specific styles
└── types/
    └── api.ts                  # TypeScript types generated from Python schemas
```

### Known Gotchas & Library Quirks
```typescript
// CRITICAL: Next.js 14 App Router specifics
// All components are Server Components by default - use 'use client' for interactive components
'use client' // Required for components using useState, useEffect, event handlers

// CRITICAL: SWR with App Router
// Must wrap SWR hooks in client components, can't use directly in server components
// Use SWRConfig in client component provider, then import in server layouts

// CRITICAL: Framer Motion performance
// Always use transform3d for animations to enable GPU acceleration
const cardVariants = {
  hover: { 
    scale: 1.05, 
    transition: { type: "spring", stiffness: 300 }
  }
}
// Use will-change CSS property sparingly and remove after animation

// CRITICAL: React-window horizontal scrolling
// Must set both width and height explicitly, overscanCount prevents empty flashes
<FixedSizeList
  layout="horizontal"
  width={1200}
  height={280}
  itemCount={items.length}
  itemSize={300}
  overscanCount={2} // IMPORTANT: prevents flash of empty content
/>

// CRITICAL: Tailwind with CSS-in-JS
// Tailwind classes work in className, but for dynamic styles use CSS variables
// Define custom properties in globals.css for theme values

// CRITICAL: Image optimization
// Always use Next.js Image component with proper sizing for performance
import Image from 'next/image'
<Image 
  src={article.imageUrl} 
  alt={article.title}
  width={300} 
  height={200}
  loading="lazy"
  placeholder="blur"
/>

// CRITICAL: Audio playback
// Use HTML5 audio with proper event handling for daily digest playback
// Implement picture-in-picture mode for background audio
```

## Implementation Blueprint

### Data Models and Structure

Create TypeScript interfaces that mirror the Python backend models for type safety:

```typescript
// types/api.ts - Generated from Python schemas
export interface Article {
  id: string;
  source_id: string;
  source: 'arxiv' | 'hackernews' | 'rss';
  title: string;
  content: string;
  url: string;
  author?: string;
  published_at: string;
  fetched_at: string;
  summary?: string;
  relevance_score?: number;
  categories: string[];
  key_points: string[];
  is_duplicate: boolean;
}

export interface DailyDigest {
  id: string;
  digest_date: string;
  summary_text: string;
  total_articles_processed: number;
  audio_url?: string;
  created_at: string;
  top_articles: Article[];
  key_themes: string[];
  notable_developments: string[];
}

export interface ApiResponse<T> {
  articles?: T[];
  total_count?: number;
  has_more?: boolean;
  digest?: DailyDigest;
  status?: string;
}
```

### Implementation Tasks (Sequential Order)

```yaml
Task 1: Project Setup and Configuration
CREATE frontend/ directory structure:
  - Initialize Next.js 14 with App Router: `npx create-next-app@latest frontend --typescript --tailwind --app`
  - MODIFY next.config.js: Add image domains for article thumbnails
  - MODIFY tailwind.config.ts: Add custom colors from color-palette.md
  - CREATE globals.css: Define CSS custom properties for themes

INSTALL dependencies:
  - npm install swr framer-motion react-window @headlessui/react lucide-react
  - npm install -D @types/react-window

Task 2: API Integration Layer  
CREATE lib/api.ts:
  - MIRROR patterns from Python routes.py endpoints
  - IMPLEMENT TypeScript fetch wrapper with error handling
  - CONFIGURE base URL and request/response types
  - ADD SWR fetcher functions for each endpoint

CREATE types/api.ts:
  - GENERATE TypeScript interfaces from Python schemas
  - ENSURE exact property name matching (snake_case from backend)
  - ADD utility types for loading states and error handling

Task 3: Core Netflix Card Component
CREATE components/cards/NetflixCard.tsx:
  - IMPLEMENT Framer Motion hover animations (scale 1.05)
  - ADD AI summary overlay with fade-in transition
  - INCLUDE relevance score badges and source attribution
  - OPTIMIZE with React.memo for performance

CREATE components/cards/CardSkeleton.tsx:
  - MATCH exact dimensions of NetflixCard (300x200px base)
  - IMPLEMENT shimmer animation effect
  - ENSURE consistent spacing and layout

Task 4: Horizontal Scrolling Infrastructure
CREATE components/rows/HorizontalRow.tsx:
  - IMPLEMENT react-window FixedSizeList with horizontal layout
  - ADD touch gesture support with momentum scrolling
  - CONFIGURE overscanCount=2 for smooth scrolling
  - HANDLE responsive sizing for different screen widths

CREATE hooks/useHorizontalScroll.ts:
  - IMPLEMENT custom hook for scroll position management
  - ADD touch event handlers for mobile swipe gestures
  - INCLUDE scroll momentum with spring physics

Task 5: Data Source Rows
CREATE components/rows/ArticleRow.tsx:
  - EXTEND HorizontalRow with article-specific logic
  - IMPLEMENT source filtering (arxiv, hackernews, rss)
  - ADD infinite scrolling with SWR pagination
  - INCLUDE real-time updates every 30 seconds

CREATE components/rows/DigestRow.tsx:
  - SPECIALIZE for daily digest audio cards
  - IMPLEMENT audio player integration
  - ADD progress tracking and playback controls

Task 6: Modal and Detail Views
CREATE components/modals/ContentModal.tsx:
  - IMPLEMENT full-screen modal with backdrop blur
  - ADD Netflix-style zoom-in entrance animation
  - INCLUDE related articles section with horizontal scroll
  - HANDLE keyboard navigation and focus management

CREATE components/modals/InAppBrowser.tsx:
  - IMPLEMENT iframe-based browser with navigation controls
  - ADD reader mode extraction for clean article viewing
  - INCLUDE bookmark functionality with local storage

Task 7: Layout and Navigation
CREATE components/ui/HeroSection.tsx:
  - IMPLEMENT cinematic header with featured content
  - ADD parallax scrolling effects on row transitions
  - INCLUDE search functionality with real-time suggestions

CREATE components/ui/Navigation.tsx:
  - IMPLEMENT floating navigation overlay
  - ADD smooth transitions between sections
  - INCLUDE theme toggle with smooth animation

Task 8: Theme and Animation System
CREATE styles/netflix-themes.css:
  - IMPLEMENT dark/light theme CSS custom properties
  - USE colors from color-palette.md (black-bean, citrine, etc.)
  - ADD smooth theme transitions with CSS transitions

CREATE lib/animations.ts:
  - DEFINE Framer Motion variants for all components
  - IMPLEMENT staggered entrance animations
  - ADD loading skeleton animations with proper timing

Task 9: Real-time Data Integration
CREATE hooks/useRealTimeUpdates.ts:
  - IMPLEMENT SWR with revalidation every 30 seconds
  - ADD optimistic UI updates for new articles
  - HANDLE notification toasts for trending content

CREATE components/providers/SWRProvider.tsx:
  - CONFIGURE global SWR settings with error handling
  - ADD fallback data for SSR compatibility
  - IMPLEMENT cache management strategies

Task 10: Main Dashboard Assembly
CREATE app/(dashboard)/page.tsx:
  - ASSEMBLE all row components in streaming layout
  - IMPLEMENT smooth scrolling between sections
  - ADD loading states and error boundaries

CREATE app/(dashboard)/layout.tsx:
  - INCLUDE navigation and hero section
  - ADD theme provider and SWR configuration
  - IMPLEMENT responsive layout with mobile optimization
```

### Per Task Implementation Details

```typescript
// Task 3: Netflix Card hover effect pseudocode
const NetflixCard: React.FC<ArticleCardProps> = ({ article }) => {
  // PATTERN: Use Framer Motion for smooth hover animations
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.div
      // CRITICAL: Use transform3d for GPU acceleration
      whileHover={{ scale: 1.05, zIndex: 10 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
    >
      <div className="relative w-[300px] h-[200px] rounded-lg overflow-hidden">
        {/* PATTERN: Next.js Image optimization */}
        <Image 
          src={article.imageUrl || '/placeholder.jpg'}
          alt={article.title}
          fill
          className="object-cover"
          loading="lazy"
        />
        
        {/* ANIMATION: AI summary overlay on hover */}
        <AnimatePresence>
          {isHovered && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="absolute inset-0 bg-black/80 p-4"
            >
              <p className="text-sm text-white">{article.summary}</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
};

// Task 4: Horizontal scrolling with virtualization
const HorizontalRow: React.FC<HorizontalRowProps> = ({ items, renderItem }) => {
  // PATTERN: Responsive sizing for different screen widths
  const [windowWidth, setWindowWidth] = useState(1200);
  
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return (
    <FixedSizeList
      layout="horizontal"
      width={windowWidth}
      height={280}
      itemCount={items.length}
      itemSize={320} // Card width + spacing
      overscanCount={2} // CRITICAL: Prevents flash of empty content
    >
      {({ index, style }) => (
        <div style={style}>
          {renderItem(items[index], index)}
        </div>
      )}
    </FixedSizeList>
  );
};

// Task 9: Real-time updates with SWR
const useRealTimeUpdates = (source?: ArticleSource) => {
  // PATTERN: SWR with automatic revalidation
  const { data, error, mutate } = useSWR(
    `/api/articles${source ? `?source=${source}` : ''}`,
    fetcher,
    {
      refreshInterval: 30000, // 30 seconds
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
      onSuccess: (newData) => {
        // PATTERN: Show notification for new articles
        if (newData.articles.length > data?.articles.length) {
          showNotification('New articles available!');
        }
      }
    }
  );
  
  return { articles: data?.articles || [], error, refresh: mutate };
};
```

### Integration Points
```yaml
API ENDPOINTS:
  - GET /articles: List articles with filtering and pagination
  - GET /articles/{id}: Get specific article details  
  - GET /digest/latest: Get latest daily digest with audio
  - GET /stats: Get aggregated statistics for dashboard
  - POST /webhook/fetch: Trigger manual article fetching

ENVIRONMENT VARIABLES:
  - NEXT_PUBLIC_API_URL: Backend API base URL
  - NEXT_PUBLIC_WS_URL: WebSocket URL for real-time updates

CSS CUSTOM PROPERTIES:
  - --color-black-bean: #230007ff (primary dark)
  - --color-citrine: #d7cf07ff (accent bright)
  - --color-fulvous: #d98324ff (secondary accent)
  - --color-turkey-red: #a40606ff (error states)
  - --color-rosewood: #5a0002ff (deep accent)

RESPONSIVE BREAKPOINTS:
  - sm: 640px (mobile landscape)
  - md: 768px (tablet)
  - lg: 1024px (desktop)
  - xl: 1280px (large desktop)
```

## Validation Loop

### Level 1: TypeScript & Linting
```bash
# Run these FIRST - fix any errors before proceeding
npx tsc --noEmit                    # TypeScript compilation check
npm run lint                        # ESLint with Next.js rules
npm run lint:fix                   # Auto-fix linting issues

# Expected: No TypeScript errors, all linting rules pass
```

### Level 2: Component Unit Tests
```typescript
// CREATE __tests__/NetflixCard.test.tsx
import { render, fireEvent, waitFor } from '@testing-library/react';
import { NetflixCard } from '../components/cards/NetflixCard';

describe('NetflixCard', () => {
  const mockArticle = {
    id: '1',
    title: 'Test Article',
    summary: 'Test summary',
    imageUrl: '/test.jpg'
  };

  test('renders article title correctly', () => {
    const { getByText } = render(<NetflixCard article={mockArticle} />);
    expect(getByText('Test Article')).toBeInTheDocument();
  });

  test('shows summary overlay on hover', async () => {
    const { getByText, getByTestId } = render(<NetflixCard article={mockArticle} />);
    const card = getByTestId('netflix-card');
    
    fireEvent.mouseEnter(card);
    await waitFor(() => {
      expect(getByText('Test summary')).toBeInTheDocument();
    });
  });

  test('handles missing image gracefully', () => {
    const articleWithoutImage = { ...mockArticle, imageUrl: undefined };
    const { container } = render(<NetflixCard article={articleWithoutImage} />);
    const img = container.querySelector('img');
    expect(img?.src).toContain('placeholder.jpg');
  });
});
```

```bash
# Run tests and iterate until passing
npm test -- --watchAll=false
# If failing: Read error, understand root cause, fix code, re-run
```

### Level 3: Integration Testing
```bash
# Start development server
npm run dev

# Test main dashboard load
curl -I http://localhost:3000
# Expected: 200 OK, page loads with content

# Test API integration
curl http://localhost:3000/api/health
# Expected: Backend API connectivity confirmed

# Test responsive design
# Open browser dev tools, test at 320px, 768px, 1024px, 1920px widths
# Expected: Layout adapts properly at all breakpoints
```

### Level 4: Performance Validation
```bash
# Run Lighthouse audit
npx lighthouse http://localhost:3000 --output html --output-path ./lighthouse-report.html

# Expected scores:
# Performance: >90
# Accessibility: >90  
# Best Practices: >90
# SEO: >80

# Core Web Vitals targets:
# LCP (Largest Contentful Paint): <2.5s
# FID (First Input Delay): <100ms
# CLS (Cumulative Layout Shift): <0.1
```

## Final Validation Checklist
- [ ] All TypeScript compilation passes: `npx tsc --noEmit`
- [ ] All tests pass: `npm test`
- [ ] No linting errors: `npm run lint`
- [ ] Responsive design works 320px-1920px
- [ ] Horizontal scrolling smooth on touch devices
- [ ] Hover animations run at 60fps
- [ ] Real-time updates work with backend API
- [ ] Theme switching animates smoothly
- [ ] Audio playback works for daily digests
- [ ] Modal navigation accessible via keyboard
- [ ] Core Web Vitals meet targets
- [ ] Images load with proper lazy loading
- [ ] Error states display user-friendly messages

---

## Anti-Patterns to Avoid
- ❌ Don't use CSS-in-JS libraries (styled-components) - use Tailwind + CSS variables
- ❌ Don't implement custom virtualization - use react-window for performance
- ❌ Don't skip 'use client' directive for interactive components
- ❌ Don't use synchronous API calls - always use SWR for data fetching
- ❌ Don't animate expensive properties (width/height) - use transforms only
- ❌ Don't load all articles at once - implement pagination and virtualization
- ❌ Don't ignore mobile experience - implement touch gestures and momentum scrolling
- ❌ Don't forget accessibility - include ARIA labels and keyboard navigation
- ❌ Don't hardcode API URLs - use environment variables
- ❌ Don't skip loading states - implement proper skeleton screens

## Confidence Score: 9/10

This PRP provides comprehensive context including:
- ✅ Complete codebase analysis and integration points
- ✅ External research on Netflix-style implementations
- ✅ Modern React/Next.js patterns (2024-2025)
- ✅ Performance optimization strategies
- ✅ Executable validation loops with specific commands
- ✅ Detailed task breakdown with pseudocode
- ✅ TypeScript patterns and type safety
- ✅ Responsive design and accessibility considerations
- ✅ Real-world gotchas and library-specific quirks

The only risk factor is the complexity of integrating multiple advanced features (virtualization + animations + real-time updates), but the sequential task approach and validation loops should enable successful iterative implementation.