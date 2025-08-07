# Netflix-Style AI News Aggregator - UX Design Document

## 1. Executive Summary

This document defines the complete user experience architecture for a Netflix-style AI news aggregator interface. The design emphasizes content discovery through horizontal scrolling, card-based layouts, and intelligent categorization while maintaining a sleek monochrome aesthetic.

### Design Principles
- **Content-First**: Large visual cards with clear hierarchy
- **Progressive Disclosure**: Details revealed on interaction
- **Familiar Patterns**: Netflix-style browsing behavior
- **Accessibility**: WCAG 2.1 AA compliance
- **Performance**: Optimized loading and smooth animations

## 2. Information Architecture

### 2.1 Site Hierarchy

```
Home (Landing)
├── Navigation Bar (Persistent)
│   ├── Brand/Logo
│   ├── Source Filters (All, ArXiv, HN, RSS, YouTube, HuggingFace, Reddit, GitHub)
│   └── Search & Actions
├── Hero Section
│   ├── Welcome Message
│   ├── Live Statistics Dashboard
│   └── Quick Actions (Refresh, Trigger Fetch)
├── Filter Controls Bar
│   ├── Relevance Score Slider
│   ├── Time Range Dropdown
│   ├── Sort Options
│   └── Order Toggle
├── Content Sections (Horizontal Scroll)
│   ├── Daily AI Digests (Audio-enabled)
│   ├── Search Results (Contextual)
│   ├── ArXiv Research Papers
│   ├── Hacker News Discussions
│   ├── RSS News Articles
│   ├── YouTube AI Videos
│   ├── HuggingFace Models
│   ├── Reddit Discussions
│   └── GitHub Tool Updates
└── Pagination Controls
```

### 2.2 User Flows

#### Primary User Journey
1. **Landing** → View hero stats and latest digest
2. **Browse** → Scroll horizontally through content rows
3. **Filter** → Adjust relevance/time filters to refine
4. **Discover** → Hover cards for quick preview
5. **Engage** → Click for modal with full details
6. **Action** → Read full article or play audio digest

#### Search Flow
1. **Initiate** → Focus search input in nav
2. **Type** → Real-time suggestions appear
3. **Execute** → Press enter or click search
4. **Results** → Dynamic search section appears
5. **Refine** → Apply filters to search results
6. **Clear** → Return to default view

## 3. Layout Specifications

### 3.1 Grid System
- **Base Grid**: 8px unit system
- **Container**: Max-width 1920px, centered
- **Margins**: 24px (mobile), 48px (tablet), 64px (desktop)
- **Gutter**: 16px between cards
- **Card Width**: 320px (fixed for optimal readability)

### 3.2 Responsive Breakpoints
```css
Mobile:    320px - 767px   (1-2 cards visible)
Tablet:    768px - 1023px  (2-3 cards visible)
Desktop:   1024px - 1439px (3-4 cards visible)
Wide:      1440px+         (4-6 cards visible)
```

## 4. Component Specifications

### 4.1 Navigation Bar
```
Height: 64px
Background: rgba(26, 26, 26, 0.95) with blur(10px)
Position: Fixed top, z-index: 100
Behavior: Solid background on scroll
```

**Structure:**
- Logo area (180px width)
- Source tabs (flex-grow)
- Search bar (300px expanded, 200px collapsed)
- Admin button (48px)

### 4.2 Article Cards

**Dimensions:**
```
Width: 320px (fixed)
Height: 420px (standard), 480px (with video)
Border-radius: 8px
Padding: 16px
```

**States:**
- **Default**: Subtle shadow, grayscale
- **Hover**: Scale(1.05), shadow elevation, show preview
- **Active**: Scale(0.98), highlight border
- **Loading**: Skeleton animation

**Content Structure:**
```
├── Image/Placeholder (320x180px)
│   └── Source Badge (top-left)
│   └── Duration/Count (bottom-right, if video)
├── Title (2 lines max, 18px font)
├── Meta Info (14px, gray)
│   ├── Source Name
│   ├── Time Ago
│   └── Relevance Score (color-coded)
├── Categories (12px badges)
├── Summary (3 lines, 14px)
└── Key Points (2 items, 12px)
```

### 4.3 Content Rows

**Layout:**
```
Padding: 24px vertical
Overflow-x: auto (hidden scrollbar)
Scroll-behavior: smooth
Gap: 16px between cards
```

**Scroll Controls:**
- Left/Right arrows (40px circles)
- Appear on hover
- Disabled state at boundaries
- Keyboard navigation (arrow keys)

### 4.4 Article Modal

**Dimensions:**
```
Width: 90vw (max 900px)
Height: 90vh (max 700px)
Position: Fixed center
Background: #1a1a1a
Border-radius: 12px
```

**Content Areas:**
1. **Header** (80px)
   - Title (24px font)
   - Close button (top-right)

2. **Metadata Bar** (48px)
   - Source, Date, Relevance
   - Category badges

3. **Body** (flex-grow)
   - AI Summary (expandable)
   - Key Points (bullet list)
   - AI Analysis (collapsible)
   - Related Articles (horizontal scroll)

4. **Footer** (64px)
   - View Original (primary action)
   - Re-analyze (secondary)
   - Share options

### 4.5 Audio Player (Digest)

**Mini Player (in card):**
```
Height: 48px
Play/Pause button (32px)
Progress bar (flex-grow)
Time display (60px)
```

**Global Player (bottom bar):**
```
Position: Fixed bottom
Height: 80px
Background: #1a1a1a with blur
Full controls: Play, Progress, Volume, Speed, Close
```

## 5. Interaction Patterns

### 5.1 Hover Behaviors
- **Cards**: Elevate + scale 1.05 (200ms ease-out)
- **Buttons**: Background lighten 10%
- **Links**: Underline animation (left to right)
- **Rows**: Show scroll arrows

### 5.2 Click Interactions
- **Card Click**: Open modal (fade + scale animation)
- **Outside Modal**: Close modal
- **ESC Key**: Close any overlay
- **Source Tab**: Filter + smooth scroll to section

### 5.3 Scroll Behaviors
- **Horizontal Scroll**: Momentum-based with snap points
- **Card Snap**: Align to container edge
- **Parallax Hero**: Subtle depth on vertical scroll
- **Infinite Scroll**: Load more at 80% scroll position

### 5.4 Loading States
```
1. Initial: Full-page skeleton
2. Section: Row skeleton with shimmer
3. Card: Individual placeholder animation
4. Modal: Content skeleton while fetching details
```

## 6. Animation Specifications

### 6.1 Timing Functions
```css
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

### 6.2 Animation Durations
- **Micro**: 100ms (hovers, state changes)
- **Short**: 200ms (card interactions)
- **Medium**: 300ms (modal open/close)
- **Long**: 500ms (page transitions)

### 6.3 Specific Animations
```css
/* Card Hover */
transform: scale(1.05);
box-shadow: 0 8px 24px rgba(0,0,0,0.4);
transition: all 200ms ease-out;

/* Modal Entry */
animation: modalFadeIn 300ms ease-out;
@keyframes modalFadeIn {
  from { 
    opacity: 0; 
    transform: scale(0.95) translateY(20px);
  }
  to { 
    opacity: 1; 
    transform: scale(1) translateY(0);
  }
}

/* Skeleton Loading */
background: linear-gradient(90deg, 
  #333 25%, 
  #404040 50%, 
  #333 75%
);
background-size: 200% 100%;
animation: shimmer 1.5s infinite;
```

## 7. Color System

### 7.1 Monochrome Palette
```css
--black: #000000;
--gray-900: #0a0a0a;
--gray-800: #1a1a1a;
--gray-700: #2a2a2a;
--gray-600: #333333;
--gray-500: #4d4d4d;
--gray-400: #666666;
--gray-300: #808080;
--gray-200: #999999;
--gray-100: #b3b3b3;
--gray-50: #cccccc;
--white: #ffffff;
```

### 7.2 Semantic Colors (Relevance Scores)
```css
--relevance-high: #10b981;   /* 80-100% */
--relevance-medium: #f59e0b; /* 60-79% */
--relevance-low: #ef4444;    /* Below 60% */
```

### 7.3 Component Applications
- **Backgrounds**: Primary black, card gray-800
- **Text**: Primary white, secondary gray-200
- **Borders**: gray-600 default, gray-400 hover
- **Shadows**: Pure black with varying opacity

## 8. Typography

### 8.1 Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
             'Helvetica Neue', Arial, sans-serif;
```

### 8.2 Type Scale
```css
--text-xs: 12px;   /* Badges, captions */
--text-sm: 14px;   /* Body, meta info */
--text-base: 16px; /* Default paragraph */
--text-lg: 18px;   /* Card titles */
--text-xl: 20px;   /* Section headers */
--text-2xl: 24px;  /* Modal titles */
--text-3xl: 32px;  /* Hero heading */
--text-4xl: 48px;  /* Feature display */
```

### 8.3 Font Weights
- **Light (300)**: Large display text
- **Regular (400)**: Body text
- **Medium (500)**: UI elements, buttons
- **Bold (700)**: Headers, emphasis

## 9. Accessibility

### 9.1 Keyboard Navigation
```
Tab: Navigate through interactive elements
Arrow Keys: Navigate within card rows
Enter/Space: Activate buttons/links
Escape: Close modals/overlays
Shift+Tab: Reverse navigation
```

### 9.2 Screen Reader Support
- Semantic HTML5 elements
- ARIA labels for icons
- Live regions for dynamic content
- Skip navigation links
- Focus indicators (2px white outline)

### 9.3 Color Contrast
- Text on dark: Minimum 7:1 ratio
- Interactive elements: 4.5:1 ratio
- Relevance indicators with text labels

## 10. Mobile Adaptations

### 10.1 Touch Interactions
- **Swipe**: Horizontal scroll through cards
- **Pull-to-refresh**: Trigger data update
- **Long press**: Show context menu
- **Pinch**: Zoom article text in modal

### 10.2 Mobile Layout Changes
```
- Navigation: Hamburger menu
- Cards: Full width with 16px margins
- Filters: Collapsible accordion
- Modal: Full screen with gesture dismiss
- Audio player: Minimized bottom bar
```

## 11. Performance Optimizations

### 11.1 Loading Strategy
1. **Critical CSS**: Inline above-fold styles
2. **Lazy Loading**: Images load on scroll proximity
3. **Virtual Scrolling**: Render visible cards only
4. **Prefetch**: Next row data on hover
5. **Service Worker**: Cache static assets

### 11.2 Image Optimization
```
- WebP format with JPEG fallback
- Responsive srcset for different screens
- Blur-up placeholder technique
- Lazy loading with Intersection Observer
```

## 12. State Management

### 12.1 Application States
```javascript
{
  view: 'home' | 'filtered' | 'search',
  filters: {
    source: 'all' | SourceType,
    relevance: 0-100,
    timeRange: hours | null,
    sortBy: 'date' | 'relevance',
    order: 'asc' | 'desc'
  },
  modal: {
    open: boolean,
    articleId: string | null
  },
  audio: {
    playing: boolean,
    digestId: string | null,
    progress: 0-100
  },
  loading: {
    sections: Set<string>,
    modal: boolean
  }
}
```

## 13. Error Handling

### 13.1 Error States
- **Network Error**: Retry button with offline message
- **No Results**: Friendly empty state illustration
- **Load Failure**: Graceful degradation to text
- **API Error**: Toast notification with details

### 13.2 Recovery Actions
```
- Automatic retry (3 attempts)
- Manual refresh option
- Fallback to cached data
- Error boundary for React components
```

## 14. Implementation Guidelines

### 14.1 Component Library Structure
```
components/
├── layout/
│   ├── Navigation.tsx
│   ├── Hero.tsx
│   └── FilterBar.tsx
├── content/
│   ├── ContentRow.tsx
│   ├── ArticleCard.tsx
│   └── DigestCard.tsx
├── overlays/
│   ├── ArticleModal.tsx
│   └── AudioPlayer.tsx
└── common/
    ├── Button.tsx
    ├── Skeleton.tsx
    └── Toast.tsx
```

### 14.2 CSS Architecture
- **Methodology**: CSS Modules with utility classes
- **Variables**: CSS custom properties for theming
- **Animation**: Framer Motion for complex interactions
- **Reset**: Normalize.css base

### 14.3 Testing Checklist
- [ ] Keyboard navigation flow
- [ ] Screen reader announcements
- [ ] Touch gesture support
- [ ] Loading performance (<3s)
- [ ] Animation smoothness (60fps)
- [ ] Error recovery paths
- [ ] Responsive breakpoints

## 15. Metrics & Success Criteria

### 15.1 Performance Metrics
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3.5s
- **Cumulative Layout Shift**: <0.1
- **Animation FPS**: >60fps

### 15.2 User Engagement
- **Card Hover Rate**: >70%
- **Modal Open Rate**: >40%
- **Audio Play Rate**: >25%
- **Filter Usage**: >30%

### 15.3 Accessibility Score
- **Lighthouse**: >95
- **WAVE**: 0 errors
- **axe DevTools**: Pass all checks

## Appendix: Design Tokens

```javascript
const designTokens = {
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    xxxl: '64px'
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    full: '9999px'
  },
  shadows: {
    sm: '0 2px 4px rgba(0,0,0,0.2)',
    md: '0 4px 8px rgba(0,0,0,0.3)',
    lg: '0 8px 16px rgba(0,0,0,0.4)',
    xl: '0 16px 32px rgba(0,0,0,0.5)'
  },
  transitions: {
    fast: '100ms',
    base: '200ms',
    slow: '300ms',
    slower: '500ms'
  }
};
```

---

This design document provides comprehensive specifications for implementing a Netflix-style AI news aggregator with modern UX patterns, accessibility compliance, and performance optimization. The monochrome design system ensures visual consistency while the interaction patterns create an engaging, familiar user experience.