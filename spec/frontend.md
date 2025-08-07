## FEATURE:

- Netflix-style content discovery interface with horizontal scrolling card rows for AI/ML news aggregation
- Data source organization via horizontal card rows (ArXiv papers, HackerNews stories, RSS feeds, daily digests)
- Interactive hover animations with card expansion revealing AI-generated summaries and key insights
- Netflix-inspired content detail screens with options to read AI summary or open in-app browser
- Dedicated daily digest audio row featuring voice summary cards with integrated audio playback
- Smooth micro-animations and transitions throughout the interface without overwhelming users
- Real-time content updates with seamless card additions and subtle notification animations
- Modern React/Next.js frontend with TypeScript, Tailwind CSS, and Framer Motion animations
- Mobile-responsive design optimized for touch interactions and gesture-based navigation
- **Monochrome design system** with black/white/gray palette for professional aesthetic

## QUICK START GUIDE:

### Recommended Implementation Order:
1. **Start with static HTML prototype** (like hybrid.html) to validate design
2. **Move to Next.js** once design is approved
3. **Add animations last** - get layout working first
4. **Use mock data initially** - don't wait for backend API

### Key Design Decisions:
- **Monochrome only**: No colors except black/white/gray
- **No icons/emojis**: Use text labels instead
- **Large text**: Prioritize readability over density
- **Horizontal scrolling**: Core interaction pattern
- **Modals over navigation**: Keep users on main page

## FRONTEND COMPONENT TIERS:

### MVP Components (Netflix-Style Interface):
1. **Streaming Layout** (Next.js 14+ App Router)
   - **Borderless Netflix header** with gradient fade to transparent background
   - **Hero section** with large featured content and prominent call-to-action
   - Horizontal scrolling card rows with smooth momentum scrolling
   - **Navigation integrated in header** (Browse, Papers, News, Videos, Models, Reddit, Tools)
   - **Filters positioned below hero section** (Time Range, Relevance slider)
   - Mobile-optimized touch gestures and swipe navigation
   - Implementation: TypeScript, Tailwind CSS, Framer Motion

2. **Content Card Rows** (Horizontal Scrolling by Data Source)
   - **ArXiv Papers Row**: Academic-styled cards with research paper aesthetics
   - **HackerNews Row**: Tech-focused cards with community engagement indicators
   - **RSS Feeds Row**: Blog-style cards grouped by publication source
   - **Daily Digest Row**: Premium audio cards with voice summary playback
   - **YouTube Videos Row**: Video thumbnail cards with view counts
   - **HuggingFace Models Row**: Model cards with download counts
   - **Reddit Discussions Row**: Community posts with upvote counts
   - **GitHub Tools Row**: Repository cards with star counts
   - Implementation: React components with virtualization for performance

3. **Interactive Article Cards** (Netflix-Style Content Cards)
   - **Card dimensions**: 320px width (w-80), flexible height
   - Hover expansion animation (scale 1.05) with smooth transitions
   - **Gradient placeholder backgrounds** for source branding
   - **Clean typography**: Title (2 lines), metadata, category tags, summary (3 lines)
   - Relevance score badges with percentage display
   - **Netflix-style scroll arrows** that appear on container hover
   - Click-to-detail transition with Netflix-style content modal
   - Implementation: CSS transforms for 60fps animations

### Tier 1: Enhanced Streaming Experience:
**Content Detail Screens (Netflix-Style Modals):**
- Full-screen content modal with dark overlay background
- **Clean modal layout**: Title, source/time/relevance metadata, category tags
- **AI summary section** prominently displayed with proper spacing
- **Key points section** with bullet points for quick scanning
- **Full content section** for detailed reading
- **"Read Full Article" button** that opens original source
- **Close button (×)** in top-right corner
- Click outside modal to close functionality
- Smooth modal transitions (fade-in with scale)

**Advanced Animation System:**
- Parallax scrolling effects on row transitions
- Staggered card entrance animations when loading new content
- Micro-interactions on hover states (glow effects, shadow elevation)
- Loading skeleton animations that match card layouts
- Real-time notification toasts that slide in from top-right
- Smooth momentum scrolling with spring-based physics

### Tier 2: Premium Streaming Features:
**Personalization & Discovery:**
- AI-powered content recommendations based on reading history
- Personalized row ordering based on user preferences
- "Continue Reading" row for partially read articles
- Custom collections and playlist creation for articles
- Smart notifications for trending topics in user's interest areas

**Advanced Audio Features:**
- Picture-in-picture audio player for daily digests
- Background audio playback while browsing other content
- Audio speed controls and bookmarking within audio content
- Queue system for multiple daily digest episodes
- Voice-activated navigation and search functionality

### Implementation Priority Notes:
- **Netflix-Style MVP**: Focus on horizontal scrolling rows and basic hover animations first
- **Animation Performance**: Use CSS transforms and Framer Motion for 60fps animations
- **Mobile Touch Experience**: Implement swipe gestures and momentum scrolling early
- **Card Virtualization**: Essential for performance with large content libraries
- **Accessibility**: Ensure all hover effects have keyboard and screen reader alternatives

## API REQUIREMENTS FOR FRONTEND:

Based on the frontend needs, the backend API should provide:

### Article Data Structure:
```json
{
  "id": "unique_id",
  "title": "Article Title",
  "source": "arxiv|hackernews|rss|youtube|huggingface|reddit|github",
  "source_name": "ArXiv Papers",  // Display name
  "url": "https://original-source.com",
  "published_at": "2024-01-15T10:30:00Z",
  "relevance_score": 85,  // 0-100 percentage
  "categories": ["Natural Language Processing", "Deep Learning"],
  "summary": "AI-generated 2-3 sentence summary",
  "key_points": [
    "First key technical insight",
    "Second important finding",
    "Third critical observation"
  ],
  "content": "Full article content or extended description",
  "metadata": {
    "author": "Author Name",
    "publication": "Publication Name",
    "read_time": "5 min",
    "engagement": {  // Optional, source-specific
      "comments": 245,
      "upvotes": 1234,
      "views": 45000,
      "downloads": 12500
    }
  }
}
```

### Required API Endpoints:
1. **GET /api/v1/articles** - Paginated articles with filters
   - Query params: source, time_range, min_relevance, page, limit
   - Response: Articles grouped by source for row display

2. **GET /api/v1/articles/search** - Full-text search
   - Query params: q, sources[], min_relevance
   - Response: Flat list of matching articles

3. **GET /api/v1/digest/latest** - Latest daily digest
   - Response: Digest with audio_url and transcript

4. **GET /api/v1/sources/stats** - Source statistics
   - Response: Article counts per source, last update times

## EXAMPLES:

In the `examples/` folder, create the following examples to demonstrate frontend functionality:

- `examples/components/NetflixCard.tsx` - Netflix-style article card with hover expansion and AI summary overlay
- `examples/components/HorizontalRow.tsx` - Horizontal scrolling row component with momentum physics
- `examples/components/ContentModal.tsx` - Full-screen Netflix-style content detail modal with in-app browser
- `examples/components/AudioDigestCard.tsx` - Premium audio card for daily digest playback with integrated player
- `examples/components/HeroSection.tsx` - Cinematic header with featured content and subtle branding
- `examples/hooks/useHoverAnimation.ts` - Custom hook for Netflix-style card hover effects
- `examples/hooks/useHorizontalScroll.ts` - Touch-optimized horizontal scrolling with momentum
- `examples/hooks/useInAppBrowser.ts` - In-app browser functionality for seamless article reading
- `examples/pages/StreamingDashboard.tsx` - Main Netflix-style layout with multiple content rows
- `examples/animations/cardAnimations.ts` - Framer Motion animation variants for cards and modals
- `examples/utils/streamingApi.ts` - API client optimized for real-time content streaming
- `examples/styles/netflixThemes.css` - Cinematic dark/light themes with premium color palettes

## DOCUMENTATION:

- Next.js 14+ documentation: https://nextjs.org/docs
- React 18+ documentation: https://react.dev/
- TypeScript handbook: https://www.typescriptlang.org/docs/
- Tailwind CSS documentation: https://tailwindcss.com/docs
- Framer Motion animations: https://www.framer.com/motion/
- Headless UI components: https://headlessui.com/
- SWR data fetching: https://swr.vercel.app/
- react-window virtualization: https://react-window.vercel.app/
- Zustand state management: https://docs.pmnd.rs/zustand/getting-started/introduction
- Lucide React icons: https://lucide.dev/guide/packages/lucide-react
- Web Audio API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- CSS Transform animations: https://developer.mozilla.org/en-US/docs/Web/CSS/transform
- Touch events and gestures: https://developer.mozilla.org/en-US/docs/Web/API/Touch_events
- Vercel deployment: https://vercel.com/docs/deployments/overview
- Existing backend API: http://localhost:8000/docs (when running locally)

## LEARNINGS FROM MOCK IMPLEMENTATIONS:

Based on our three mock implementations (V0, MockupV2, Qwen-mock, and Hybrid), here are the key learnings:

### Design System Best Practices:
- **Monochrome palette works best**: Black (#000000), grays (#1a1a1a, #333333, #666666), white (#ffffff)
- **No colors or emojis**: Keep the interface professional and focused on content
- **Font sizes matter**: Use larger, readable typography (text-lg for titles, text-base for body)
- **Proper spacing is crucial**: Use consistent padding (p-5 to p-8) for breathing room

### Layout Patterns That Work:
- **Hero section placement**: Large hero with featured content immediately grabs attention
- **Filter positioning**: Time/relevance filters work best under hero, not in header
- **Header style**: Borderless, gradient-fade headers feel more modern than bordered ones
- **Navigation placement**: Inline navigation in header (Netflix-style) over separate nav bars
- **Card dimensions**: 320px width (w-80) provides optimal content display

### Interaction Patterns:
- **Hover effects**: Scale 1.05 with shadow provides satisfying feedback
- **Scroll arrows**: Should only appear on container hover, not always visible
- **Modal behavior**: Click card to open, × button or outside click to close
- **Audio player**: Fixed bottom bar that appears only when playing
- **Category tags**: Rounded pills (rounded-full) look more modern than squares

### Content Organization:
- **Source grouping**: Separate rows for each source type (ArXiv, HN, etc.)
- **Metadata display**: "Source • Time ago • Relevance%" format works well
- **Summary length**: 3-line clamp for card summaries, full text in modals
- **Key points**: Bullet points in modals for quick scanning

### Technical Implementation Notes:
- **Pure HTML/CSS/JS can work**: Complex React isn't always necessary for prototypes
- **Tailwind CSS**: Provides rapid iteration and consistent styling
- **CSS transforms**: Essential for smooth 60fps animations
- **Virtualization**: Not needed for MVP with limited cards per row

## OTHER CONSIDERATIONS:

- **Netflix-Style Performance**: Prioritize 60fps animations using CSS transforms and GPU acceleration
- **Horizontal Scroll Optimization**: Use `react-window` for virtualization to handle thousands of cards efficiently
- **Touch Gesture Implementation**: 
  - Momentum scrolling with spring physics for natural feel
  - Swipe-to-navigate between content rows on mobile
  - Touch feedback with haptic vibration on supported devices
  - Prevent scroll bounce and rubber-band effects on iOS
- **Animation Hierarchy**: 
  - Hover animations (scale 1.05, glow effects) have highest priority
  - Entrance animations (stagger effects) use optimal timing curves
  - Loading skeletons match exact card dimensions to prevent layout shift
  - Use `transform3d` and `will-change` for GPU acceleration
- **Netflix-Style State Management**: 
  - Cache viewed content positions for seamless navigation
  - Preload adjacent cards in horizontal rows for instant display
  - Persist user's scroll position within each row
  - Background prefetch of content modal data on hover
- **In-App Browser Integration**: 
  - Iframe-based browser with full navigation controls
  - Reader mode extraction for clean article viewing
  - Bookmark synchronization with main application state
  - Progressive web app features for offline article caching
- **Audio Experience Optimization**: 
  - Picture-in-picture audio player that persists across navigation
  - Audio preloading for instant playbook on daily digest cards
  - Background audio with system media controls integration
  - Automatic pause/resume based on user focus and visibility
- **Cinematic Theme System**: 
  - Netflix-inspired dark theme as primary with subtle gradients
  - Light theme optimized for reading with high contrast
  - Smooth theme transitions using CSS custom properties
  - Adaptive colors based on featured content imagery
- **Accessibility for Streaming UI**: 
  - Keyboard navigation with logical tab order through horizontal rows
  - Screen reader announcements for dynamic content updates
  - High contrast focus indicators for card navigation
  - Reduced motion preferences respected for all animations
- **Performance Monitoring**: 
  - Core Web Vitals tracking specifically for horizontal scroll performance
  - Animation frame rate monitoring to maintain 60fps
  - Memory usage tracking for virtualized lists
  - Network usage optimization for real-time content updates