# Frontend Developer - Development Guidelines & Standards (Next.js 14 + TypeScript + Tailwind + shadcn/ui + TanStack Query)

## Role Overview
As a Senior Frontend Developer on the CiteGuard project, you are responsible for:
- **Building & Shipping Features**: Developing user-facing features from requirements to production
- **Code Quality**: Writing clean, maintainable, and well-documented code
- **Architecture**: Designing component structures following SOLID principles (adapted for React)
- **Performance**: Optimizing application performance and bundle sizes
- **UI/UX Excellence**: Creating intuitive, accessible, and professional interfaces for lawyers reviewing privileged material
- **Security**: Implementing security best practices and never leaking privileged content
- **Testing**: Writing comprehensive tests for components and features
- **Code Review**: Reviewing peer code and providing constructive feedback
- **Collaboration**: Working with backend developers, designers, and product managers

This document serves as your comprehensive guide for development standards, best practices, and rules to follow while building features and reviewing code.

> **⚠️ Domain criticality notice:** CiteGuard's UI is used by lawyers reviewing privileged AI-generated legal content. UI bugs are not inconveniences — a mis-rendered flag, an unlabeled override, or a copy-pasted piece of document text into an error toast becomes a malpractice and compliance problem. Treat every surface accordingly.

**Stack:** Next.js 14 (App Router) · TypeScript 5+ · Tailwind CSS · shadcn/ui · TanStack Query · react-hook-form + zod · Zustand (minimal) · Clerk (auth) · Vitest + React Testing Library · Playwright · Vercel

---

## Table of Contents

### Core Principles & Architecture
1. [SOLID Principles (Adapted for React)](#1-solid-principles-adapted-for-react)
2. [Code Duplication (Zero Tolerance)](#2-code-duplication-zero-tolerance)
3. [Performance Optimization](#3-performance-optimization)

### Technology-Specific Best Practices
4. [Next.js + React Best Practices](#4-nextjs--react-best-practices)
5. [TanStack Query + Client State Best Practices](#5-tanstack-query--client-state-best-practices)
6. [Tailwind + shadcn/ui Best Practices](#6-tailwind--shadcnui-best-practices)
7. [Routing & Navigation (App Router)](#7-routing--navigation-app-router)

### Implementation Standards
8. [API Integration & Data Fetching](#8-api-integration--data-fetching)
9. [UI/UX Best Practices](#9-uiux-best-practices)
10. [Security Best Practices](#10-security-best-practices)
11. [TypeScript Best Practices](#11-typescript-best-practices)

### Quality Assurance
12. [Testing Requirements](#12-testing-requirements)
13. [Code Quality & Maintainability](#13-code-quality--maintainability)

### Project-Specific Guidelines
14. [Specific Project Rules (CiteGuard)](#14-specific-project-rules-citeguard)
15. [Build & Deployment](#15-build--deployment)

### Workflow & Process
16. [Development Workflow](#16-development-workflow)
17. [Code Quality Checklist](#17-code-quality-checklist)
18. [Rejection Criteria](#18-rejection-criteria-development--code-review)
19. [Collaboration & Communication](#19-collaboration--communication)

### Philosophy & Mindset
- [Developer Mindset](#-developer-mindset)
- [Final Note](#final-note)

---

## 1. SOLID PRINCIPLES (ADAPTED FOR REACT)

### 1.1 Single Responsibility Principle (SRP)
- **RULE**: Each component/hook/function has ONE reason to change
- **CHECK**: Components handle only presentation or orchestration, not both
- **CHECK**: Server Components fetch and render; Client Components handle interactivity — keep them separate
- **CHECK**: Custom hooks contain ONE piece of reusable logic
- **CHECK**: Utility functions do ONE thing only
- **CHECK**: API service functions handle ONE endpoint / ONE resource
- **CHECK**: Zustand stores (when used) manage ONE concern
- **CHECK**: Context providers manage ONE concern
- **REJECT**: Components mixing data-fetching, business logic, and UI
- **REJECT**: Custom hooks doing multiple unrelated things
- **REJECT**: Components over 300 lines (split into smaller components)
- **EXAMPLE**: Split `ReviewQueue` into `ReviewQueueContainer` (data + state) and `ReviewQueueView` (pure presentation); or use a Server Component parent for data + a Client Component child for interactivity.

### 1.2 Open/Closed Principle (OCP)
- **RULE**: Open for extension, closed for modification
- **CHECK**: Use composition over complex prop matrices
- **CHECK**: Use render props / `children` for flexible behavior
- **CHECK**: Use compound components for complex UI (e.g., `<DocumentDetail>`, `<DocumentDetail.Header>`, `<DocumentDetail.FlagList>`)
- **CHECK**: Extend shadcn/ui primitives; don't fork them
- **REJECT**: Adding conditional rendering for every new variant
- **REJECT**: Modifying existing components for new features — compose instead
- **REJECT**: Switch statements based on a `variant` prop exploding past 3 branches
- **EXAMPLE**: Use `<Table>`, `<Table.Header>`, `<Table.Row>` (shadcn/ui pattern) instead of a `Table` with 20 props

### 1.3 Liskov Substitution Principle (LSP)
- **RULE**: Component variants must be interchangeable
- **CHECK**: All variants of a component accept same core props
- **CHECK**: Component APIs are consistent across variants
- **CHECK**: Child components honor parent component contracts
- **REJECT**: Variants requiring completely different props
- **REJECT**: Overriding behavior that breaks parent expectations
- **EXAMPLE**: `<Button>`, `<Button variant="primary">`, `<Button variant="destructive">` all accept `onClick`, `disabled`, `asChild`

### 1.4 Interface Segregation Principle (ISP)
- **RULE**: Components should not depend on props they don't use
- **CHECK**: Keep prop interfaces small (max 10 props)
- **CHECK**: Split components if too many props
- **CHECK**: Use composition to avoid prop drilling
- **CHECK**: Group related props into objects (e.g., `document` instead of `documentId`, `documentStatus`, `documentText`…)
- **REJECT**: Components with 15+ props
- **REJECT**: Passing entire objects when only 1–2 fields needed
- **REJECT**: "God components" accepting everything
- **EXAMPLE**: Instead of 15 props, pass a `document` object with the fields relevant to that component

### 1.5 Dependency Inversion Principle (DIP)
- **RULE**: Depend on abstractions, not concretions
- **CHECK**: Components depend on hooks / generated API client, not direct fetch/axios calls
- **CHECK**: Use dependency injection via props/context where applicable
- **CHECK**: Abstract API calls into a generated TypeScript client layer (`lib/api/`)
- **CHECK**: Use hooks to abstract complex logic (`useDocument`, `useFlags`, `useReviewerAction`)
- **REJECT**: Direct `fetch` / `axios` calls in components
- **REJECT**: Hard-coded API URLs in components
- **REJECT**: Tightly coupled components
- **EXAMPLE**: Component uses `useDocument(documentId)` hook, which uses TanStack Query + generated client — not direct API calls

---

## 2. CODE DUPLICATION (ZERO TOLERANCE)

### 2.1 Duplication Detection
- **RULE**: No code duplication beyond 3 lines
- **CHECK**: Similar components must share a base component or shadcn/ui primitive
- **CHECK**: Repeated JSX patterns must be extracted to components
- **CHECK**: Repeated logic must be extracted to custom hooks
- **CHECK**: Repeated styles must use Tailwind utilities or shared component variants
- **CHECK**: Repeated API calls must go through the generated client + TanStack Query hooks
- **REJECT**: Copy-pasted components with minor differences
- **REJECT**: Repeated `useEffect` logic across components
- **REJECT**: Similar form validation across forms (share zod schemas)

### 2.2 Component Extraction
- **RULE**: Extract reusable UI into shared components
- **CHECK**: shadcn/ui primitives + small wrappers → `components/ui/`
- **CHECK**: Common CiteGuard patterns → `components/common/`
- **CHECK**: Feature-specific components → `app/<feature>/_components/`
- **CHECK**: Layout components → `components/layout/`
- **CHECK**: Form components → `components/forms/`
- **MANDATE**: `SeverityBadge`, `FlagRow`, `DocumentStatusPill`, `ReviewActionButtons`, `EmptyState` are shared components — never reimplement locally
- **REJECT**: Inline flag-row UI duplicated across pages
- **REJECT**: Similar card layouts not extracted

### 2.3 Custom Hooks for Logic Reuse
- **RULE**: Extract repeated logic to custom hooks
- **CHECK**: Form handling → `react-hook-form` + shared zod schemas (no custom `useForm`)
- **CHECK**: Server state → TanStack Query hooks (`useDocument`, `useFlags`, `useReviewerAction`, `useAuditExport`)
- **CHECK**: Authentication → `useUser()` from Clerk + a thin `useCurrentFirm()` wrapper
- **CHECK**: Pagination → `usePagination()` (URL-synced via `useSearchParams`)
- **CHECK**: Debounced search → `useDebouncedValue()`
- **CHECK**: Modal state → shadcn/ui Dialog with its own open state (avoid global modal state)
- **CHECK**: Keyboard shortcuts → `useHotkeys()` (via `react-hotkeys-hook` or similar)
- **REJECT**: Repeated `useState` + `useEffect` patterns
- **REJECT**: Same API-fetch logic in multiple components

### 2.4 Utility Functions & Constants
- **RULE**: No magic numbers or repeated logic
- **CHECK**: Date formatting → `lib/utils/date.ts` (use `date-fns`; one consistent format per context)
- **CHECK**: Validation schemas → `lib/schemas/` (shared zod schemas between client and server)
- **CHECK**: String utilities → `lib/utils/string.ts`
- **CHECK**: API client + helpers → `lib/api/`
- **CHECK**: Constants → `lib/constants/` (`SEVERITY_ORDER`, `DEFAULT_PAGE_SIZE`, etc.)
- **REJECT**: Inline `new Date().toLocaleString(...)` formatting
- **REJECT**: Hard-coded status strings (use enums / const literals from shared types)
- **REJECT**: Repeated validation logic

---

## 3. PERFORMANCE OPTIMIZATION

### 3.1 Server Components First
- **RULE**: Default to React Server Components; reach for Client Components deliberately
- **CHECK**: Pages and layouts that only fetch + render remain Server Components
- **CHECK**: Add `"use client"` only to components that need state, effects, browser APIs, or event handlers
- **CHECK**: Push `"use client"` as far down the tree as possible (keep most of the tree server-rendered)
- **REJECT**: Marking the entire page `"use client"` for one interactive button
- **REJECT**: Fetching data in Client Components when a Server Component could do it
- **REJECT**: Importing heavy client-only libraries into Server Components (will fail build)

### 3.2 Component Rendering Optimization
- **RULE**: Minimize unnecessary re-renders (inside Client Components)
- **CHECK**: Use `React.memo` for expensive pure components (flag rows in long queues)
- **CHECK**: Use `useMemo` for expensive calculations
- **CHECK**: Use `useCallback` for functions passed as props to memoized children
- **CHECK**: Avoid inline object/array creation as props to memoized children
- **CHECK**: Use stable, unique keys in lists (flag IDs, document IDs — never index)
- **REJECT**: Creating new objects/arrays as props to memoized components without memoization
- **REJECT**: Inline arrow functions on memoized components
- **REJECT**: Using index as key for dynamic lists
- **REJECT**: Premature memoization that just adds noise (measure first)

### 3.3 Code Splitting & Lazy Loading
- **RULE**: Load code only when needed
- **CHECK**: Route-based code splitting is automatic with App Router — don't fight it
- **CHECK**: Use `next/dynamic` with `{ ssr: false }` for client-only heavy components (PDF preview, rich editors)
- **CHECK**: Lazy load modals/dialogs that are rarely opened
- **CHECK**: Analyze bundle with `@next/bundle-analyzer` regularly
- **TARGET**: Initial JS bundle < 500KB (gzipped)
- **TARGET**: Route transitions < 200ms on a warm cache
- **REJECT**: Importing all routes into one bundle
- **REJECT**: Heavy libraries loaded upfront
- **MANDATE**: PDF preview, chart libraries, and rich editors are dynamically imported

### 3.4 List Rendering Optimization
- **RULE**: Optimize large lists
- **CHECK**: Pagination for lists > 50 items (server-driven via URL params)
- **CHECK**: Virtualization (TanStack Virtual) for lists > 100 items — critical for the audit log browser
- **CHECK**: Memoize list items when they're expensive to render
- **CHECK**: Stable keys from IDs (never index)
- **CHECK**: Debounce search inputs (300ms)
- **REJECT**: Rendering 1000+ items without virtualization
- **REJECT**: Filtering large lists on every keystroke
- **REJECT**: Re-creating list items on every parent re-render

### 3.5 Asset Optimization
- **RULE**: Optimize all static assets
- **CHECK**: Use `next/image` for every image (automatic WebP/AVIF, lazy loading, responsive sizes)
- **CHECK**: Use `next/font` for fonts (subset, preload, no FOUT)
- **CHECK**: Use `lucide-react` for icons (tree-shakeable)
- **CHECK**: Compress/optimize static images before committing
- **TARGET**: Each image < 100KB
- **REJECT**: Using raw `<img>` for non-trivial images
- **REJECT**: Loading all images upfront
- **REJECT**: Custom icons as one-off image files when a Lucide icon fits

### 3.6 State Management Performance
- **RULE**: Efficient state updates
- **CHECK**: Use local `useState` for component-specific UI state
- **CHECK**: Use URL search params for filter/sort/pagination state (shareable + shareable)
- **CHECK**: Use TanStack Query for server state (documents, flags, audit log, firms, users)
- **CHECK**: Use Zustand **only** when justified (rare in CiteGuard; Clerk handles auth state)
- **CHECK**: Normalize TanStack Query keys (e.g., `['document', documentId]`, `['flags', { documentId }]`)
- **CHECK**: Use selectors (`select` option in TanStack Query) to prevent unnecessary re-renders
- **REJECT**: Storing derived/server data in local state
- **REJECT**: Putting everything in a global Zustand store
- **REJECT**: Context provider values that change on every parent render (causes cascade)

### 3.7 Network Performance
- **RULE**: Minimize and optimize network requests
- **CHECK**: TanStack Query caches server responses; tune `staleTime` per resource (5 min for documents list, 30s for a live queue, ∞ for court data lookups since backend caches)
- **CHECK**: Request deduplication happens automatically with TanStack Query
- **CHECK**: Use optimistic updates for reviewer actions (approve/override/reject) — this is critical for queue throughput
- **CHECK**: Prefetch the next document in the queue while the current one is being reviewed
- **CHECK**: Avoid request waterfalls — use Server Component parallel fetching or `Promise.all` in route handlers
- **REJECT**: Making the same API call multiple times in the same render
- **REJECT**: No loading states
- **REJECT**: Sequential requests that could run in parallel

---

## 4. NEXT.JS + REACT BEST PRACTICES

### 4.1 Server vs Client Components
- **RULE**: Server Components are the default; Client Components are opt-in
- **CHECK**: Pages and layouts are Server Components unless they require interactivity at the top
- **CHECK**: Add `"use client"` at the leaf components that actually need interactivity
- **CHECK**: Data fetching is ideally done in Server Components (or in route handlers)
- **CHECK**: TanStack Query is used in Client Components for live/mutating data; RSC fetches for static/initial data
- **REJECT**: Putting `"use client"` at the top of a page that has one interactive button — push it down
- **REJECT**: Using Client Components just to "match older patterns"

### 4.2 Component Design
- **RULE**: Well-structured, maintainable components
- **CHECK**: Functional components only (no class components; error boundaries live in `error.tsx`)
- **CHECK**: Components max 300 lines (split if larger)
- **CHECK**: Max 10 props per component
- **CHECK**: TypeScript for all components
- **CHECK**: Prop interfaces typed; prefer `type` aliases or `interface` consistently project-wide
- **CHECK**: Components are pure where possible
- **REJECT**: Class components
- **REJECT**: Mixing logic, data-fetching, and presentation in a single Client Component
- **REJECT**: Components without typed props

### 4.3 Hooks Usage
- **RULE**: Follow hooks rules and best practices
- **CHECK**: Only call hooks at the top level
- **CHECK**: Only call hooks in React functions or custom hooks
- **CHECK**: Custom hooks start with `use`
- **CHECK**: `useEffect` dependency arrays are complete
- **CHECK**: Cleanup in `useEffect` for subscriptions/timers
- **CHECK**: Use `useLayoutEffect` only when you need synchronous DOM updates
- **REJECT**: Conditional hook calls
- **REJECT**: Missing cleanup in `useEffect`
- **REJECT**: Empty dep array when deps exist
- **REJECT**: Ignoring ESLint `exhaustive-deps` warnings

### 4.4 State Management Strategy
- **RULE**: Use the appropriate state solution for scope
- **CHECK**: Local UI state → `useState`
- **CHECK**: Complex local state → `useReducer`
- **CHECK**: Feature-level shared state → Context (cautiously) or Zustand slice
- **CHECK**: URL-worthy state (filters, sort, pagination, search) → `useSearchParams`
- **CHECK**: Server state → TanStack Query
- **CHECK**: Auth/user state → Clerk (`useUser`, `useAuth`)
- **REJECT**: Prop drilling beyond 2 levels (use Context or composition)
- **REJECT**: Zustand for trivial local UI state
- **REJECT**: Multiple sources of truth for the same data

#### When TanStack Query is the answer (almost always for server data):
- Documents list, document detail, flags for a document
- Firm/user/API-key listings
- Audit log pages
- Any mutation (`approveFlag`, `overrideFlag`, `finalizeDocument`, `exportAudit`)

#### When a Zustand store is justified (rare in V1):
- Cross-route UI state that genuinely can't live in a URL or component
- Command palette / shortcut registry
- Evaluator-in-flight progress that spans multiple pages

#### When URL state (`useSearchParams`) is the answer:
- Queue filters (severity, status, submitter)
- Sort order
- Pagination cursor
- Search text

### 4.5 Event Handlers
- **RULE**: Efficient event handling
- **CHECK**: Descriptive handler names (`handleApprove`, `handleOverride`, `handleFinalize`)
- **CHECK**: Memoize handlers passed to memoized children
- **CHECK**: `preventDefault` on form submit
- **CHECK**: `stopPropagation` only when justified
- **CHECK**: Debounce expensive handlers (search inputs at 300ms)
- **REJECT**: Inline arrow functions on memoized list items
- **REJECT**: Event handlers containing business logic (extract to hooks/mutations)

### 4.6 Conditional Rendering
- **RULE**: Clean, readable conditionals
- **CHECK**: Use `&&` for simple conditions
- **CHECK**: Use ternary for binary choices
- **CHECK**: Extract complex conditionals to named variables or functions
- **CHECK**: Use early returns in component bodies
- **REJECT**: Nested ternaries (>2 levels)
- **REJECT**: Complex boolean logic inside JSX
- **EXAMPLE**: `const canFinalize = allFlagsResolved && userCanReview; return canFinalize && <FinalizeButton />;`

### 4.7 Form Handling
- **RULE**: Robust form implementation
- **CHECK**: `react-hook-form` for all non-trivial forms (override reasons, firm settings, invites)
- **CHECK**: `zod` schemas for validation — **shared** between client and server (single source of truth)
- **CHECK**: Display field-level errors inline, with `aria-describedby`
- **CHECK**: Disable submit while the mutation is in flight
- **CHECK**: Handle loading, success, and error states explicitly
- **CHECK**: Show a toast on success; keep the error inline on failure
- **CHECK**: Enforce rules client-side that the server also enforces (`OVERRIDE` reason ≥ 10 chars)
- **REJECT**: Uncontrolled forms without a library
- **REJECT**: Client-only validation (server must re-validate)
- **REJECT**: Silent submission failures

---

## 5. TANSTACK QUERY + CLIENT STATE BEST PRACTICES

> **Note:** CiteGuard does not use Redux Toolkit. Server state lives in TanStack Query; the rare global client state lives in a small Zustand store.

### 5.1 Query Design
- **RULE**: Consistent, normalized query keys
- **CHECK**: Key conventions: `['documents', { firmId, status, page }]`, `['document', documentId]`, `['flags', { documentId }]`, `['audit-log', { firmId, cursor }]`
- **CHECK**: One query hook per resource (`useDocument`, `useDocuments`, `useFlags`, `useAuditLog`)
- **CHECK**: Query hooks live in `lib/queries/` co-located with the feature where appropriate
- **CHECK**: Use `select` to derive shaped data and narrow re-render dependencies
- **CHECK**: Tune `staleTime` intentionally per resource (live queue: 10–30s; document detail: 5 min; court data: Infinity — backend caches)
- **REJECT**: Ad-hoc inline `useQuery` calls scattered across components
- **REJECT**: Magic string keys like `['x']` with no schema

### 5.2 Mutations & Invalidation
- **RULE**: Explicit, predictable invalidation
- **CHECK**: Use `useMutation` for every write (`approveFlag`, `overrideFlag`, `finalizeDocument`, `generateExport`)
- **CHECK**: On success, invalidate only affected queries (`queryClient.invalidateQueries({ queryKey: ['flags', { documentId }] })`)
- **CHECK**: Use optimistic updates for reviewer actions (instant UI feedback is critical for throughput)
- **CHECK**: Always provide a rollback path in `onError`
- **CHECK**: Toast on error with a retry affordance
- **REJECT**: `queryClient.invalidateQueries()` with no key (nukes everything)
- **REJECT**: Mutations without error handling
- **REJECT**: Optimistic updates without rollback

### 5.3 TanStack Query Configuration
- **RULE**: Sensible defaults
- **CHECK**: Global `QueryClient` with `retry: (failureCount, error) => isNetworkError(error) && failureCount < 2` (don't retry 4xx)
- **CHECK**: `refetchOnWindowFocus: true` for live queue; `false` for rarely-changing data
- **CHECK**: Dev tools (`@tanstack/react-query-devtools`) enabled only in dev
- **CHECK**: Hydration set up for Server Component → Client Component data handoff
- **REJECT**: Retrying 4xx errors (it just delays the user's bad input feedback)

### 5.4 Zustand Stores (When Justified)
- **RULE**: Small, focused, typed stores
- **CHECK**: One store per concern (e.g., `useCommandPaletteStore`)
- **CHECK**: Selectors used at the consumer site (`useStore(s => s.isOpen)`) — prevents over-rendering
- **CHECK**: Full TypeScript typing on state and actions
- **CHECK**: Persist only what must survive refresh; never persist auth tokens or document content
- **REJECT**: Stores over 100 lines (split or rethink)
- **REJECT**: Using Zustand when URL state or component state would work
- **REJECT**: Storing server data in Zustand (that's TanStack Query's job)

### 5.5 Selector & Derived Data
- **RULE**: Efficient data selection
- **CHECK**: Derive with `select` in TanStack Query or selectors in Zustand
- **CHECK**: Co-locate selectors with their store/query
- **CHECK**: Memoize expensive transforms with `useMemo`
- **REJECT**: Deriving the same data in multiple components
- **REJECT**: Selectors with side effects

---

## 6. TAILWIND + SHADCN/UI BEST PRACTICES

### 6.1 Utility Class Usage
- **RULE**: Leverage Tailwind utilities effectively
- **CHECK**: Utility classes directly in JSX
- **CHECK**: Group related utilities (layout, spacing, color, typography) in a consistent order
- **CHECK**: Responsive modifiers (`sm:`, `md:`, `lg:`) used deliberately
- **CHECK**: Hover/focus/active states via modifiers
- **CHECK**: Use `cn()` helper (from shadcn/ui) for conditional classes
- **REJECT**: Inline `style` attributes
- **REJECT**: Long className strings (>15 utilities) — extract a component
- **REJECT**: Custom CSS when a Tailwind utility exists

### 6.2 shadcn/ui Primitives
- **RULE**: Build on shadcn/ui; don't reinvent
- **CHECK**: Import primitives from `components/ui/` (the shadcn/ui source)
- **CHECK**: Customize via variants (`cva`, class-variance-authority) — not via forking
- **CHECK**: Keep our wrappers thin (e.g., `SeverityBadge` wraps `Badge` with our severity color mapping)
- **CHECK**: Document variants with JSDoc so the design system stays navigable
- **REJECT**: Forking and duplicating shadcn/ui primitives
- **REJECT**: Wrapping every primitive "just to be safe"
- **EXAMPLE**: `SeverityBadge` takes `severity: "CRITICAL" | "HIGH" | "MEDIUM" | "ADVISORY"` and maps to `<Badge variant="destructive|warning|amber|secondary">`

### 6.3 Component Extraction
- **RULE**: Extract repeated utility patterns
- **CHECK**: Create reusable components for repeated patterns
- **CHECK**: Use `@apply` very sparingly (only for complex primitives that couldn't be utilities)
- **CHECK**: Document component variants
- **REJECT**: Copy-pasting the same className strings across files
- **REJECT**: Overusing `@apply` (defeats the purpose of utilities)

### 6.4 Responsive Design
- **RULE**: Desktop-first, with graceful mobile read-only fallback
- **CHECK**: Primary use case is lawyer at a desktop — design for 1280px+
- **CHECK**: Works cleanly down to 1024px
- **CHECK**: Below 1024px, show a read-only dashboard/queue view with an explicit notice: "Review is supported on desktop only in V1"
- **CHECK**: Touch targets ≥ 44px on any surface that does render on mobile (notifications list, read-only views)
- **CHECK**: Minimum 16px font size where interactive to prevent iOS zoom
- **REJECT**: Pretending we support full mobile review flows in V1
- **REJECT**: Breaking the desktop experience in pursuit of mobile parity

### 6.5 Theme Customization
- **RULE**: Consistent design system
- **CHECK**: Colors, spacing, radii, and typography defined in `tailwind.config.ts`
- **CHECK**: Semantic tokens via shadcn/ui's CSS variables (`--primary`, `--destructive`, etc.)
- **CHECK**: Severity palette is a distinct, named set — red/orange/amber/blue, never green
- **CHECK**: Use theme tokens consistently; don't reach for arbitrary hex values
- **REJECT**: Hard-coded hex colors in utility classes (`bg-[#ff0000]`)
- **REJECT**: Inconsistent color usage
- **REJECT**: Green used to indicate "good" or "approved" (culturally wrong for this product)

### 6.6 Performance
- **RULE**: Optimize Tailwind for production
- **CHECK**: Content paths in `tailwind.config.ts` cover every file that uses utility classes
- **CHECK**: Monitor CSS bundle size
- **TARGET**: CSS bundle < 50KB (gzipped)
- **REJECT**: Missing content paths (will produce bloated or broken CSS)

---

## 7. ROUTING & NAVIGATION (APP ROUTER)

### 7.1 App Router Architecture
- **RULE**: Clean, conventional routing with the App Router
- **CHECK**: Routes live under `app/`; co-locate route-specific components under `_components/`
- **CHECK**: Use `layout.tsx` for shared chrome, `page.tsx` for route content
- **CHECK**: Use `loading.tsx` for route-level loading UI (skeletons)
- **CHECK**: Use `error.tsx` for route-level error boundaries
- **CHECK**: Use `not-found.tsx` for 404s
- **CHECK**: Route groups (`(group)`) for logical grouping without URL impact
- **CHECK**: Parallel routes / intercepting routes only when genuinely useful (reviewer side panel is a candidate)
- **REJECT**: One giant client-side router
- **REJECT**: Loading spinners without a `loading.tsx` or Suspense boundary

### 7.2 Navigation Best Practices
- **RULE**: User-friendly navigation
- **CHECK**: Use `next/link` for internal navigation (never `<a>`)
- **CHECK**: Use `useRouter` from `next/navigation` for imperative navigation
- **CHECK**: `next/link` prefetches by default — keep it enabled for the queue
- **CHECK**: Preserve scroll position across route transitions where appropriate
- **CHECK**: Active-link styling via `usePathname`
- **CHECK**: Breadcrumbs for deep routes (firm settings, audit detail)
- **REJECT**: `<a>` tags for internal links (full page reloads)
- **REJECT**: Full page reloads on in-app navigation
- **REJECT**: No indication of the current route

### 7.3 Route Parameters & Search Params
- **RULE**: Proper URL state management
- **CHECK**: Dynamic segments for resource IDs (`/documents/[documentId]`)
- **CHECK**: Search params for filters/sort/pagination (`?severity=critical&sort=created_at&page=2`)
- **CHECK**: Validate route params (zod on the server, typed helpers on the client)
- **CHECK**: Handle missing/invalid params gracefully (404 or redirect with message)
- **REJECT**: Complex objects serialized into the URL (use state)
- **REJECT**: Unvalidated params
- **REJECT**: Ignoring URL state on page load (always rehydrate from URL)

### 7.4 Route Protection
- **RULE**: Enforce auth and roles at the route level
- **CHECK**: Use Clerk middleware to protect authenticated routes
- **CHECK**: Role-gated routes (e.g., `/firm/settings/users` requires ADMIN) checked in the layout or page
- **CHECK**: Unauthorized access redirects to a clear "not authorized" page, not a silent 404
- **REJECT**: Relying on UI hiding alone — route protection must exist at the server/middleware layer

---

## 8. API INTEGRATION & DATA FETCHING

### 8.1 API Client Layer
- **RULE**: Centralize all API calls
- **CHECK**: A single generated TypeScript client (from the backend OpenAPI schema) in `lib/api/`
- **CHECK**: Backend is the source of truth; client is regenerated on schema change (CI enforces)
- **CHECK**: Base URL from `NEXT_PUBLIC_API_URL`
- **CHECK**: Request interceptor attaches the Clerk session token
- **CHECK**: Response interceptor normalizes errors to our `CiteGuardApiError` type
- **REJECT**: Direct `fetch` / `axios` in components
- **REJECT**: Scattered API configuration
- **REJECT**: Hard-coded API URLs

### 8.2 TanStack Query Hooks Over Raw Calls
- **RULE**: Every client-side API call goes through a TanStack Query hook
- **CHECK**: Queries for reads (`useDocument`, `useFlags`, `useAuditLog`)
- **CHECK**: Mutations for writes (`useApproveFlag`, `useOverrideFlag`, `useFinalizeDocument`)
- **CHECK**: Query keys follow the conventions in §5.1
- **REJECT**: `fetch(...)` inside a component
- **REJECT**: Mutations without invalidation strategy

### 8.3 Error Handling
- **RULE**: Comprehensive error handling
- **CHECK**: Every mutation has `onError` that shows a toast with the server's error code + friendly message
- **CHECK**: 401 → Clerk handles; redirect to sign-in
- **CHECK**: 403 → show inline "You don't have permission" message; do not reveal resource existence
- **CHECK**: 404 → route to `not-found.tsx`
- **CHECK**: 429 → backoff with a "try again in X" message
- **CHECK**: 5xx → generic "Something went wrong, we've been notified" + Sentry reports
- **CHECK**: **Never** include document content in any error UI
- **REJECT**: Unhandled promise rejections
- **REJECT**: Generic "Error occurred" messages with no action
- **REJECT**: Surfacing raw server error bodies (may contain references to privileged data)

### 8.4 Loading States
- **RULE**: Always show loading feedback
- **CHECK**: Skeleton screens on initial route load (via `loading.tsx`)
- **CHECK**: In-place loading on mutations (`isPending` on the `useMutation` result)
- **CHECK**: Disable submit/action buttons during mutation
- **CHECK**: Progress indicator for long operations (audit export, evaluator run)
- **REJECT**: Blank screens during loading
- **REJECT**: Jumping UI when data loads
- **REJECT**: Multiple submissions possible

### 8.5 Caching Strategy
- **RULE**: Efficient, predictable caching
- **CHECK**: `staleTime` tuned per resource
- **CHECK**: Stale-while-revalidate is the default feel
- **CHECK**: Clear all queries on sign-out (`queryClient.clear()`)
- **CHECK**: Prefetch the next document in queue when hovering "next"
- **REJECT**: Fetching the same data repeatedly in one render
- **REJECT**: No cache invalidation on mutations
- **REJECT**: Never-expiring caches for data that clearly changes

---

## 9. UI/UX BEST PRACTICES

### 9.1 Accessibility (MANDATORY)
- **RULE**: WCAG 2.1 Level AA compliance, minimum
- **CHECK**: Semantic HTML (`<button>`, not `<div role="button">`)
- **CHECK**: Proper heading hierarchy (h1 → h2 → h3)
- **CHECK**: Alt text on all images (`next/image` `alt` required)
- **CHECK**: ARIA labels on icon-only buttons
- **CHECK**: Full keyboard navigation (tab order, Escape closes dialogs, Enter submits)
- **CHECK**: Visible focus indicators (don't suppress outline without a replacement)
- **CHECK**: Color contrast ≥ 4.5:1 for text (lawyers skew older; contrast matters)
- **CHECK**: Form labels associated with inputs (`htmlFor`/`id` or wrapped)
- **CHECK**: Errors announced to screen readers (`aria-live="polite"` on error summary)
- **CHECK**: Never convey meaning by color alone (always pair severity color with text/icon)
- **REJECT**: `<div>` / `<span>` used as buttons
- **REJECT**: Missing alt text
- **REJECT**: Keyboard traps
- **REJECT**: Color-only information
- **MANDATE**: Test with keyboard navigation on every new component

### 9.2 User Feedback
- **RULE**: Clear, timely feedback for every action
- **CHECK**: Toasts for non-blocking feedback (flag approved, document exported)
- **CHECK**: Inline error messages for form failures
- **CHECK**: Loading spinners on button click (inside the button, not separate)
- **CHECK**: Confirm dialogs for destructive/irreversible actions (finalize, delete user)
- **CHECK**: Disable buttons post-click to prevent double-submit
- **REJECT**: Silent failures
- **REJECT**: No feedback after form submission
- **REJECT**: Cryptic error messages

### 9.3 Form UX
- **RULE**: User-friendly forms
- **CHECK**: Validate on blur; don't harass users on every keystroke
- **CHECK**: Inline error display
- **CHECK**: Required fields marked visibly
- **CHECK**: Helpful placeholder text (not duplicating the label)
- **CHECK**: Appropriate input types (email, tel, url)
- **CHECK**: `autoComplete` attributes on common fields
- **CHECK**: Save progress for long forms (draft endpoints where supported)
- **CHECK**: Success/error feedback clearly distinguished
- **REJECT**: Validating on every keystroke
- **REJECT**: Clearing the form on validation error
- **REJECT**: No required-field indication
- **REJECT**: Generic error messages

### 9.4 Loading & Empty States
- **RULE**: Handle all states gracefully
- **CHECK**: Skeleton screens match the final layout
- **CHECK**: Spinners inside buttons for actions
- **CHECK**: Empty states include the reason and a next action ("No flagged documents — submit one from your AI tool to see results here")
- **CHECK**: "No results" views for filtered queues
- **CHECK**: Paginated loading states don't flash the entire list
- **REJECT**: Blank screens while loading
- **REJECT**: Empty tables with no explanation
- **REJECT**: Infinite spinners without fallback on error

### 9.5 Mobile UX (V1: Read-Only)
- **RULE**: Mobile is a read-only surface in V1
- **CHECK**: Below 1024px, show a responsive read-only dashboard + queue view
- **CHECK**: Explicit notice: "Full review requires a desktop" — with link to email themselves the document
- **CHECK**: Touch targets ≥ 44px
- **CHECK**: No horizontal scrolling
- **CHECK**: Prevent zoom on focus (`font-size >= 16px` on inputs)
- **REJECT**: Attempting to cram the full review UX onto mobile
- **REJECT**: Desktop tables without a mobile-friendly card/stacked view

### 9.6 Performance Perception
- **RULE**: Make it feel fast
- **CHECK**: Optimistic UI on reviewer actions (approve/override/reject respond instantly)
- **CHECK**: Prefetch on hover for queue items
- **CHECK**: Progressive rendering (skeleton → data) rather than long blank pauses
- **CHECK**: Smooth, subtle transitions (avoid heavy animations — this is a professional tool)
- **REJECT**: Blocking UI during operations
- **REJECT**: Slow, janky animations
- **REJECT**: No indication of progress on long tasks

### 9.7 Professional Tone (CiteGuard-Specific)
- **RULE**: This is a compliance tool, not a game
- **CHECK**: No emoji in the UI
- **CHECK**: No gamification or achievement patterns
- **CHECK**: No "Great job!" / "You're on fire!" micro-copy
- **CHECK**: Neutral, direct language ("Flag approved" — not "Nice work approving that flag! 🎉")
- **CHECK**: Severity color language: CRITICAL = red, HIGH = orange, MEDIUM = amber, ADVISORY = blue. Never green.
- **CHECK**: Density over whitespace — lawyers review high volume; show 20+ queue items without scroll
- **REJECT**: Emoji, stickers, illustrations of smiling characters
- **REJECT**: Gamification (streaks, badges, points)
- **REJECT**: Casual copy ("Oops!", "Let's go!", "Awesome!")
- **REJECT**: Sparse/whitespace-heavy layouts that force excessive scrolling

### 9.8 Keyboard-First UX (CiteGuard-Specific)
- **RULE**: Every reviewer action has a keyboard shortcut
- **CHECK**: Document published shortcut set: `A` = Approve, `O` = Override, `R` = Reject, `D` = Defer, `J`/`K` = next/previous flag, `N` = next document, `?` = show shortcuts
- **CHECK**: Shortcuts shown in tooltips and a `?` help overlay
- **CHECK**: Shortcuts never trigger when a text input is focused
- **CHECK**: Focus management moves to the next flag after an action completes
- **REJECT**: Mouse-only flows for frequent reviewer actions
- **REJECT**: Undocumented hidden shortcuts

---

## 10. SECURITY BEST PRACTICES

### 10.1 XSS Prevention
- **RULE**: Prevent cross-site scripting
- **CHECK**: React escapes by default — rely on it
- **CHECK**: Never use `dangerouslySetInnerHTML` on user-supplied content
- **CHECK**: If HTML rendering is ever needed, sanitize with DOMPurify
- **CHECK**: Validate and sanitize inputs before sending to backend
- **REJECT**: `dangerouslySetInnerHTML` with user content
- **REJECT**: Injecting user input directly into the DOM
- **REJECT**: `eval()` / `new Function()` with user input

### 10.2 Authentication & Authorization
- **RULE**: Secure authentication flow
- **CHECK**: Clerk handles sessions (httpOnly cookies); never store tokens in `localStorage`
- **CHECK**: Middleware protects routes; UI gating is secondary
- **CHECK**: Clear TanStack Query cache on sign-out
- **CHECK**: Hide role-gated UI, but **always** verify server-side too
- **CHECK**: Token refresh handled by Clerk transparently
- **REJECT**: Storing sensitive tokens client-side manually
- **REJECT**: Relying on UI hiding alone for authorization
- **REJECT**: No token expiration handling

### 10.3 Data Validation
- **RULE**: Validate all user input
- **CHECK**: zod schemas validate every form
- **CHECK**: Same zod schemas used on the server (shared)
- **CHECK**: Validate file inputs (type, size, magic bytes where applicable)
- **CHECK**: Sanitize any content rendered back to the user
- **REJECT**: Trusting user input
- **REJECT**: Skipping client-side validation (poor UX)
- **REJECT**: Client-only validation (server must re-validate)

### 10.4 Privileged Data Handling (CiteGuard-Specific)
- **RULE**: Treat every document as privileged attorney-client material
- **CHECK**: Never log document content in browser console, Sentry, or analytics
- **CHECK**: Error toasts show error codes and friendly messages — never the originating document text
- **CHECK**: Mask sensitive fields (API keys, email in logs, user IDs in logs)
- **CHECK**: HTTPS enforced (Vercel does this; verify headers)
- **CHECK**: No document text stored in `localStorage`, `sessionStorage`, IndexedDB, or Zustand persist
- **CHECK**: Sentry `beforeSend` strips known-sensitive fields
- **REJECT**: Logging any document-derived text
- **REJECT**: Exposing API keys in client bundles (use `NEXT_PUBLIC_` only for non-secret values)
- **REJECT**: Persisting document content across sessions client-side

### 10.5 Third-Party Dependencies
- **RULE**: Secure dependency management
- **CHECK**: `pnpm audit` passing in CI
- **CHECK**: Dependencies kept up-to-date (Dependabot/Renovate)
- **CHECK**: Review package reputation before adding
- **CHECK**: `pnpm-lock.yaml` committed
- **REJECT**: Installing unknown or unmaintained packages
- **REJECT**: Ignoring critical vulnerabilities
- **REJECT**: Using deprecated packages

---

## 11. TYPESCRIPT BEST PRACTICES

### 11.1 Type Safety
- **RULE**: Leverage TypeScript's type system fully
- **CHECK**: `strict: true` in `tsconfig.json`
- **CHECK**: No `any` (use `unknown` and narrow)
- **CHECK**: Props typed for every component
- **CHECK**: Function parameters and return types typed (explicit for exports)
- **CHECK**: Types for API responses come from the generated client — single source of truth
- **CHECK**: `interface` for object shapes, `type` for unions/aliases — pick a convention and be consistent
- **REJECT**: Using `any` to bypass errors
- **REJECT**: `@ts-ignore` / `@ts-expect-error` without a linked ticket and comment
- **REJECT**: Disabling strict mode

### 11.2 Component Typing
- **RULE**: Properly typed components
- **CHECK**: Prefer explicit `function Component(props: Props)` over `React.FC` (avoids implicit children)
- **CHECK**: Define prop interfaces separately, exported if reused
- **CHECK**: Use generics for reusable components (`<Table<TRow>>`)
- **CHECK**: Type `children` as `React.ReactNode` when needed
- **CHECK**: Type event handlers precisely (`React.MouseEvent<HTMLButtonElement>`)
- **EXAMPLE**:
  ```typescript
  type ButtonProps = {
    onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
    children: React.ReactNode;
    disabled?: boolean;
    variant?: "primary" | "secondary" | "destructive";
  };
  ```

### 11.3 Hooks Typing
- **RULE**: Type custom hooks properly
- **CHECK**: Explicit return types on custom hooks
- **CHECK**: Parameters typed
- **CHECK**: Generics for flexible hooks (`useList<TItem>`)
- **CHECK**: Infer types from usage when it clarifies

### 11.4 TanStack Query Typing
- **RULE**: Fully typed queries and mutations
- **CHECK**: Query functions return well-typed promises; TanStack Query infers from there
- **CHECK**: Mutation variables and return types explicit
- **CHECK**: API response types come from the generated client — do not redefine

---

## 12. TESTING REQUIREMENTS

### 12.1 Unit Testing Components
- **RULE**: Comprehensive component testing
- **TARGET**: 70%+ component coverage
- **CHECK**: Test user-observable behavior, not internals
- **CHECK**: Test conditional rendering
- **CHECK**: Test prop variations
- **CHECK**: Use **Vitest** + **React Testing Library**
- **CHECK**: Use accessibility-first queries (`getByRole`, `getByLabelText`) — they double as a11y tests
- **CHECK**: Mock TanStack Query via a fresh `QueryClient` per test
- **CHECK**: Mock the generated API client for components that mutate
- **REJECT**: Testing implementation details
- **REJECT**: Snapshot tests as the only tests
- **REJECT**: Skipping interaction tests

### 12.2 Testing Best Practices
- **RULE**: Maintainable, reliable tests
- **CHECK**: Test behavior, not structure
- **CHECK**: Use user-centric queries (`getByRole`, `getByLabelText`)
- **CHECK**: Avoid asserting on internal state
- **CHECK**: Test error and loading states explicitly
- **CHECK**: Cleanup happens automatically with RTL; don't over-engineer it
- **CHECK**: Never assert on generated IDs, dates, or non-deterministic output
- **REJECT**: Brittle tests that break on refactors
- **REJECT**: Tests depending on timers without `vi.useFakeTimers`
- **REJECT**: Flaky tests

### 12.3 Hook Testing
- **RULE**: Test custom hooks
- **CHECK**: Use `renderHook` from RTL
- **CHECK**: Test return values across input variations
- **CHECK**: Test cleanup behavior
- **CHECK**: Test hooks that use TanStack Query inside a `QueryClientProvider` wrapper

### 12.4 Integration & E2E Testing
- **RULE**: Test real user flows
- **CHECK**: Component integration via RTL (submit a form → assert toast → assert query invalidation)
- **CHECK**: Critical user journeys with **Playwright**:
  - Sign in → submit document → see flags → review → finalize → download audit PDF
  - Invite user → role assignment → permissions enforced
- **CHECK**: Run Playwright against a seeded staging environment
- **CHECK**: Tests stable enough to run in CI on every PR

---

## 13. CODE QUALITY & MAINTAINABILITY

### 13.1 Naming Conventions
- **RULE**: Clear, consistent naming
- **CHECK**: Components: PascalCase (`ReviewQueue`, `DocumentDetailView`, `FirmDashboard`)
- **CHECK**: Files: PascalCase for components (`ReviewQueue.tsx`), kebab-case for utilities (`format-date.ts`)
- **CHECK**: Hooks: camelCase with `use` prefix (`useDocument`, `useApproveFlag`)
- **CHECK**: Functions: camelCase (`handleApprove`, `formatDate`)
- **CHECK**: Constants: UPPER_SNAKE_CASE (`API_BASE_URL`, `MAX_DOCUMENT_SIZE`)
- **CHECK**: Booleans: `is`/`has`/`should`/`can` prefix (`isResolved`, `hasPendingFlags`, `canFinalize`)
- **CHECK**: Event handlers: `handle`/`on` prefix (`handleApprove`, `onFlagOverride`)
- **REJECT**: Abbreviations (`doc`, `usr`, `btn`, `flg`)
- **REJECT**: Generic names (`data`, `temp`, `helper`)

### 13.2 File Organization
- **RULE**: Logical, scalable structure (App Router convention)
- **STRUCTURE**:
  ```
  src/
    ├── app/                              # App Router
    │   ├── (auth)/                       # Route group (sign-in, sign-up)
    │   ├── (authenticated)/              # Route group requiring auth
    │   │   ├── layout.tsx                # Firm shell (nav, sidebar)
    │   │   ├── dashboard/
    │   │   ├── queue/
    │   │   │   ├── page.tsx
    │   │   │   ├── loading.tsx
    │   │   │   └── _components/
    │   │   ├── documents/
    │   │   │   └── [documentId]/
    │   │   │       ├── page.tsx
    │   │   │       └── _components/
    │   │   ├── audit/
    │   │   └── firm/                     # Admin settings
    │   │       ├── users/
    │   │       ├── api-keys/
    │   │       └── settings/
    │   ├── error.tsx
    │   ├── not-found.tsx
    │   └── layout.tsx                    # Root layout (fonts, providers)
    ├── components/
    │   ├── ui/                           # shadcn/ui primitives
    │   ├── common/                       # CiteGuard shared components (SeverityBadge, FlagRow, etc.)
    │   ├── layout/                       # AppShell, Sidebar, TopBar
    │   └── forms/                        # Shared form building blocks
    ├── lib/
    │   ├── api/                          # Generated API client + helpers
    │   ├── queries/                      # TanStack Query hooks
    │   ├── schemas/                      # Shared zod schemas
    │   ├── utils/                        # Utility functions
    │   ├── constants/                    # Constants
    │   └── stores/                       # Zustand stores (if any)
    ├── hooks/                            # Global custom hooks
    ├── types/                            # Global TypeScript types
    ├── middleware.ts                     # Clerk middleware
    └── styles/                           # Global styles (minimal; Tailwind handles most)
  ```
- **CHECK**: Feature-based folder structure within `app/`
- **CHECK**: One component per file
- **CHECK**: Co-locate route-specific components under `_components/`
- **CHECK**: Index files for clean imports from `components/common`, `components/ui`
- **REJECT**: All components in one folder
- **REJECT**: Deeply nested folders (>4 levels)

### 13.3 Import Organization
- **RULE**: Organized imports (enforced by ESLint + Prettier)
- **CHECK**: Group: React/Next → external libs → internal aliases (`@/components`, `@/lib`) → relative
- **CHECK**: Sort alphabetically within groups
- **CHECK**: Use absolute imports via `@/` alias for `src/`
- **EXAMPLE**:
  ```typescript
  // React / Next
  import { useState } from "react";
  import { useRouter } from "next/navigation";

  // External libraries
  import { useForm } from "react-hook-form";
  import { zodResolver } from "@hookform/resolvers/zod";

  // Internal
  import { Button } from "@/components/ui/button";
  import { SeverityBadge } from "@/components/common/severity-badge";
  import { useApproveFlag } from "@/lib/queries/flags";
  import type { Flag } from "@/types/flag";
  ```

### 13.4 Comments & Documentation
- **RULE**: Self-documenting code with strategic comments
- **CHECK**: JSDoc for exported components, hooks, and utilities
- **CHECK**: Explain "why", not "what"
- **CHECK**: Comment complex logic (optimistic update rollback, hash-chain visualization)
- **CHECK**: Document component prop contracts
- **REJECT**: Obvious comments
- **REJECT**: Commented-out code
- **REJECT**: Outdated comments
- **REJECT**: TODO without a ticket reference (`// TODO(CG-123): ...`)

### 13.5 Component Size
- **RULE**: Keep components manageable
- **CHECK**: Components max 300 lines
- **CHECK**: Extract sub-components as JSX grows
- **CHECK**: Extract logic to custom hooks
- **CHECK**: Consider Server + Client split as a size-reduction tool
- **REJECT**: 500+ line components
- **REJECT**: God components

---

## 14. SPECIFIC PROJECT RULES (CiteGuard)

### 14.1 Review Queue
- **RULE**: The queue is the core surface — it must be fast, dense, and keyboard-driven
- **CHECK**: Default sort: severity DESC, submitted_at ASC (same as backend)
- **CHECK**: Filters live in the URL (severity, status, submitter, date range, search) via `useSearchParams`
- **CHECK**: Virtualization on lists >100 items
- **CHECK**: Prefetch the next document on hover
- **CHECK**: Optimistic UI on reviewer actions; rollback on error with a clear toast
- **CHECK**: Keyboard shortcuts (`A`/`O`/`R`/`D`/`J`/`K`/`N`/`?`) implemented and discoverable
- **CHECK**: Reviewer identity is always visible — never act "as the firm," always as the authenticated user
- **REJECT**: Losing filter state on navigation
- **REJECT**: Blocking UI during a reviewer action
- **REJECT**: No indication of severity at a glance

### 14.2 Document Detail View
- **RULE**: Inline, precise, trustworthy
- **CHECK**: Document text rendered with inline highlights for each flag (severity-colored)
- **CHECK**: Clicking a highlight opens a side panel with the evaluator's explanation, severity, confidence, and action buttons
- **CHECK**: Side panel shows: evaluator name + version, raw evidence (e.g., "Citation not found in CourtListener"), suggested correction if any
- **CHECK**: Cannot "Finalize" while any flag is unresolved — button is disabled with a clear reason tooltip
- **CHECK**: Keyboard shortcuts work in the detail view (`J`/`K` move between flags)
- **CHECK**: Audit trail for the document visible on demand (read-only, chronological)
- **REJECT**: Rendering document content in any way that allows the browser to execute it
- **REJECT**: Hiding evaluator version (required for reproducibility)
- **REJECT**: Silent state changes (every state change produces a visible update + audit log entry)

### 14.3 Submission & Evaluation Status
- **RULE**: Transparent, polling-based evaluation feedback
- **CHECK**: After submission, show a "Evaluating…" state with per-evaluator progress
- **CHECK**: Poll (or subscribe via SSE) to update evaluator statuses in real-time
- **CHECK**: Partial results visible as evaluators finish (e.g., Citation Existence done while Quote Verification still runs)
- **CHECK**: Evaluator failure shown as an ADVISORY flag, not a blocker
- **CHECK**: Show total expected time-to-complete based on document size
- **REJECT**: Blocking the user on a spinner with no information
- **REJECT**: Hiding per-evaluator status
- **REJECT**: Treating evaluator timeouts as fatal

### 14.4 Audit Export UI
- **RULE**: Trustworthy, verifiable, re-downloadable
- **CHECK**: "Export audit PDF" button on Finalized documents only
- **CHECK**: Export generation is async — show progress, notify on completion
- **CHECK**: Download history visible in `firm/audit` — re-download supported, with the original hash shown
- **CHECK**: Show hash on download; offer a "Verify" page that takes a PDF and recomputes/compares the hash
- **CHECK**: Every export click produces an audit log entry server-side — reflect it in the UI
- **REJECT**: Client-side PDF generation (backend is authoritative)
- **REJECT**: Hiding the hash
- **REJECT**: Allowing export of non-Finalized documents

### 14.5 Firm Admin UI (Users, API Keys, Settings)
- **RULE**: Precise, auditable administration
- **CHECK**: Role dropdowns clearly labeled: ADMIN / REVIEWER / SUBMITTER
- **CHECK**: Confirm dialogs on destructive actions (remove user, revoke API key)
- **CHECK**: Last-admin safeguard surfaced in the UI (disable "remove" for the last admin with a tooltip)
- **CHECK**: API keys displayed once at creation with a prominent "Copy" — never shown again
- **CHECK**: Every admin action produces a toast + shows up in the audit log viewer
- **CHECK**: Self-role-change is disabled in the UI (server enforces too)
- **REJECT**: Destructive actions without confirmation
- **REJECT**: Showing API keys after initial display
- **REJECT**: Letting a user remove themselves or change their own role

### 14.6 Severity Color Language & Professional Tone
- **RULE**: Consistent, sober, accessible severity communication
- **CHECK**: CRITICAL = red, HIGH = orange, MEDIUM = amber, ADVISORY = blue
- **CHECK**: **Never** green — green implies "approved" or "safe" and is culturally wrong here
- **CHECK**: Severity conveyed by color AND icon AND text (a11y)
- **CHECK**: Tone is neutral-professional — "Flag approved" not "Great job approving that flag"
- **CHECK**: Empty/success states are informative, not celebratory
- **REJECT**: Emoji anywhere in product UI
- **REJECT**: Gamification (streaks, achievements, points)
- **REJECT**: Green as a state color

### 14.7 Privacy & No-Leak UI Invariants
- **RULE**: Don't leak privileged content
- **CHECK**: Document text is rendered only on the document detail page (authenticated + authorized)
- **CHECK**: Toasts, error messages, analytics events never include document content
- **CHECK**: No document text in `localStorage` / `sessionStorage` / IndexedDB
- **CHECK**: Analytics (if any) track **events**, not content
- **CHECK**: Page titles use document IDs, not document previews (browser history leak)
- **REJECT**: Previewing document text in notifications or the address bar

---

## 15. BUILD & DEPLOYMENT

### 15.1 Environment Configuration
- **RULE**: Proper environment management
- **CHECK**: `.env.local` for local dev (git-ignored)
- **CHECK**: Environment variables validated at startup via a zod schema (`lib/env.ts`)
- **CHECK**: `NEXT_PUBLIC_` prefix **only** for values safe to ship to the browser (never secrets)
- **CHECK**: Secrets (API keys, Clerk secret keys) live server-side only
- **CHECK**: Vercel environment variables per environment (Preview, Production)
- **REJECT**: Hardcoded API URLs
- **REJECT**: Secrets in code
- **REJECT**: Reusing the same config across environments

### 15.2 Build Optimization
- **RULE**: Optimized production builds
- **CHECK**: `next build` runs locally before pushing major changes
- **CHECK**: Bundle size inspected via `@next/bundle-analyzer`
- **CHECK**: No `console.log` in production (enforced via ESLint + Next.js `removeConsole`)
- **CHECK**: Source maps uploaded to Sentry
- **TARGET**: First Contentful Paint < 1.5s on 4G
- **TARGET**: Time to Interactive < 3.5s on 4G
- **REJECT**: Dev builds shipped to production
- **REJECT**: `console.log` in production code
- **REJECT**: Uncompressed assets

### 15.3 Error Monitoring
- **RULE**: Track production errors — without leaking privileged content
- **CHECK**: Sentry configured for the client with `beforeSend` scrubbing known-sensitive fields
- **CHECK**: Log errors with context (route, userId, firmId, requestId) — **not** document content
- **CHECK**: Performance metrics captured (Core Web Vitals)
- **CHECK**: Alert on error-rate spikes in Sentry
- **REJECT**: No error tracking in production
- **REJECT**: Silent production failures
- **REJECT**: Sending document content to any third-party monitoring service

---

## 16. DEVELOPMENT WORKFLOW

### 16.1 Feature Implementation Process
- **RULE**: Follow structured development workflow
- **STEP 1**: Understand Requirements
  - Read feature specs (V1 PRD, this document, architect rules)
  - Review designs and mockups
  - Clarify ambiguities with PM/Designer/Backend
  - Identify dependencies (API endpoints, shared components)
- **STEP 2**: Plan Implementation
  - Break feature into Server and Client Components
  - Identify reusable components
  - Plan state: URL params vs TanStack Query vs local vs Zustand
  - Estimate effort
- **STEP 3**: Setup & Scaffolding
  - Feature branch from main
  - Route structure under `app/`
  - Component placeholders + types
  - Generated API client refresh if schema changed
- **STEP 4**: Implementation
  - Build components following SOLID
  - Integrate TanStack Query hooks
  - Forms via react-hook-form + shared zod schemas
  - Error, loading, empty states explicit
  - Responsive down to 1024px; read-only on mobile
  - Accessibility baked in (keyboard, ARIA, contrast)
- **STEP 5**: Testing
  - Unit tests (Vitest + RTL)
  - Component integration tests
  - Playwright for critical flows when warranted
  - Manual test across desktop browsers
  - Keyboard-only pass
- **STEP 6**: Code Review
  - Self-review against this checklist
  - Request peer review
  - Address feedback
- **STEP 7**: Deployment
  - Vercel Preview Deployment auto-generated on PR
  - Share preview URL with PM/Designer for review
  - Merge to main → auto-deploy to staging
  - Verify in staging before production

### 16.2 Git Workflow
- **RULE**: Clean, atomic commits
- **CHECK**: Branch naming: `feature/CG-XXX-short-description`, `fix/CG-XXX-bug-description`
- **CHECK**: Conventional commits (`feat(queue): add keyboard shortcuts for review actions`)
- **CHECK**: Small, focused commits
- **CHECK**: Rebase onto main regularly
- **REJECT**: Committing `node_modules`, `.env.local`, `.next`
- **REJECT**: Large mixed-concern commits
- **REJECT**: Vague messages ("fix stuff", "updates", "wip")

### 16.3 Pull Request Guidelines
- **RULE**: High-quality PRs
- **CHECK**: Title: `[CG-XXX] Clear description`
- **CHECK**: Description covers:
  - **What**: changed
  - **Why**: (link to ticket)
  - **How**: implementation approach
  - **Testing**: unit + manual + accessibility pass
  - **Screenshots/Loom**: for any UI change
  - **Breaking changes**: explicit
- **CHECK**: Link to ticket
- **CHECK**: Self-review done
- **CHECK**: CI green (typecheck, lint, tests)
- **CHECK**: No merge conflicts
- **REJECT**: PRs > 1000 lines (split)
- **REJECT**: PRs without description or screenshots for UI changes
- **REJECT**: Failing CI

---

## 17. CODE QUALITY CHECKLIST

### Before Submitting PR or Approving Code, Verify:

#### ✅ SOLID Principles
- [ ] Single Responsibility: Components focused on one thing
- [ ] Open/Closed: Extensible through composition
- [ ] Liskov Substitution: Variants interchangeable
- [ ] Interface Segregation: No god components
- [ ] Dependency Inversion: Depends on hooks / generated client, not direct calls

#### ✅ Code Duplication
- [ ] No duplicated components or logic
- [ ] Shared components used (SeverityBadge, FlagRow, etc.)
- [ ] Logic extracted to custom hooks / TanStack Query hooks
- [ ] Shared zod schemas between client and server

#### ✅ Performance
- [ ] Server Components default; Client Components deliberate
- [ ] Memoization used where measured to matter
- [ ] Virtualization for long lists
- [ ] Dynamic imports for heavy components
- [ ] No unnecessary re-renders
- [ ] Bundle size acceptable

#### ✅ React / Next.js Best Practices
- [ ] Hooks rules followed
- [ ] Proper state management choice (URL / TanStack Query / local / Zustand)
- [ ] Forms use react-hook-form + zod
- [ ] Error boundaries via `error.tsx`

#### ✅ UI/UX
- [ ] Accessible (keyboard, ARIA, contrast)
- [ ] Loading, error, empty states covered
- [ ] Desktop-first responsive
- [ ] Keyboard shortcuts for reviewer actions
- [ ] Professional tone (no emoji, no gamification)
- [ ] Severity color language correct (no green)

#### ✅ Security & Privacy
- [ ] No `dangerouslySetInnerHTML` with user content
- [ ] No document content in logs, errors, analytics, or storage
- [ ] Auth and role gates in place (server-verified)
- [ ] Secrets not shipped to the browser

#### ✅ TypeScript
- [ ] Strict mode passes
- [ ] No `any` / `@ts-ignore` without justification
- [ ] Props and hooks typed
- [ ] API types from generated client

#### ✅ Testing
- [ ] Unit tests (behavior, not internals)
- [ ] User interactions tested via RTL
- [ ] Edge cases + error states covered
- [ ] CI green

#### ✅ Code Quality
- [ ] Naming conventions followed
- [ ] Components under 300 lines
- [ ] File organization matches structure
- [ ] Imports organized
- [ ] Meaningful comments

#### ✅ CiteGuard-Specific
- [ ] No document content in logs, toasts, analytics, storage, or URLs
- [ ] Severity colors per spec (no green)
- [ ] Reviewer actions have keyboard shortcuts
- [ ] Optimistic UI with rollback on mutations
- [ ] Mobile is read-only (no fake review UX below 1024px)

---

## 18. REJECTION CRITERIA (Development & Code Review)

### 🚫 Immediate Rejection/Rework Required

1. **Security Issues**
   - XSS vulnerabilities
   - Secrets shipped in the client bundle
   - `dangerouslySetInnerHTML` with user content
   - Tokens stored in `localStorage`

2. **Privacy Violations (CiteGuard-Specific)**
   - Document content in logs, Sentry payloads, analytics, toasts, error messages
   - Document content in `localStorage` / `sessionStorage` / IndexedDB / URL
   - Sending document content to any third-party service

3. **Critical Performance Issues**
   - Full-page Client Components for a single interactive element
   - 1000+ item lists without virtualization
   - Bundle size > 1MB (gzipped)
   - Obvious N+1 fetch waterfalls

4. **SOLID Violations**
   - Business logic in presentational components
   - God components (>500 lines)
   - Prop drilling >3 levels
   - Direct `fetch`/`axios` in components

5. **Code Duplication**
   - Copy-pasted components
   - Reimplemented `SeverityBadge`, `FlagRow`, etc.
   - Redefined API types instead of using generated ones

6. **Accessibility Failures**
   - `<div>`-as-button
   - Missing alt text
   - Poor color contrast
   - Missing keyboard handlers
   - Severity conveyed by color only

7. **React / Next.js Anti-Patterns**
   - Breaking hooks rules
   - Missing `useEffect` cleanup
   - Ignoring `exhaustive-deps`
   - Infinite render loops
   - Marking entire pages `"use client"` without need

8. **Poor Practices**
   - `any` used extensively
   - `console.log` in production code
   - Commented-out code blocks
   - No error / loading states
   - Missing TypeScript types

9. **UI/UX Issues**
   - Severity green used as "good"
   - Emoji / gamification in UI
   - Non-functional keyboard shortcuts
   - Mobile pretending to support full review flow
   - No feedback for user actions
   - Forms without validation

10. **CiteGuard-Specific**
    - UI permits finalization with unresolved flags
    - Override action without a reason field (min 10 chars)
    - Re-exportable without hash display
    - API key shown after initial creation
    - Users able to change their own role or remove themselves

---

## 19. COLLABORATION & COMMUNICATION

### 19.1 Code Review Feedback Guidelines

#### When Providing Code Review Feedback:

#### 🎯 Be Specific & Actionable
- ❌ BAD: "This component is too complex"
- ✅ GOOD: "`DocumentDetailView` is 480 lines. Extract the flag side panel into `FlagDetailPanel` and the keyboard-shortcut effects into `useReviewShortcuts()`."

#### 🎯 Explain the Principle
- ❌ BAD: "Don't do this"
- ✅ GOOD: "This violates SRP — the component does data fetching, state management, and UI. Move the data fetching to a TanStack Query hook (`useDocument`) and keep this component pure presentation."

#### 🎯 Provide Solutions
- ❌ BAD: "This will cause performance issues"
- ✅ GOOD: "Inline arrow function passed to memoized `FlagRow` defeats the memoization. Wrap with `useCallback`: `const handleApprove = useCallback((flagId) => approveFlag(flagId), [approveFlag]);`"

#### 🎯 Reference Standards
- ❌ BAD: "Use a different pattern"
- ✅ GOOD: "Follow the TanStack Query hook pattern per §5. See `useDocument` in `lib/queries/documents.ts`."

#### 🎯 Prioritize Issues
1. **P0 - Critical**: Privacy leaks, security vulnerabilities, broken functionality, accessibility blockers
2. **P1 - High**: SOLID violations, performance regressions, missing error handling
3. **P2 - Medium**: Code duplication, missing tests, maintainability
4. **P3 - Low**: Naming, formatting, minor optimizations

### 19.2 Working with Backend Developers
- **RULE**: Seamless frontend-backend collaboration
- **CHECK**: Consume the generated OpenAPI client — do not hand-write API types
- **CHECK**: Feedback on API design before implementation (pagination shape, error codes, response fields)
- **CHECK**: Align on error response format; use `error.code` for branching, not `error.message`
- **CHECK**: Share zod schemas where feasible (validation consistency)
- **CHECK**: Report API issues with a reproducer + request/response
- **CHECK**: Never work around backend bugs on the client — fix the contract
- **REJECT**: Making up API behavior assumptions
- **REJECT**: Hardcoding response shapes that diverge from the contract
- **REJECT**: Silent tolerance of backend misbehavior

### 19.3 Working with Designers
- **RULE**: Faithfully implement, and surface technical realities
- **CHECK**: Review designs before building
- **CHECK**: Ask about edge cases, error states, empty states
- **CHECK**: Communicate technical constraints early (e.g., "virtualization means we can't use a CSS grid that requires sibling selectors here")
- **CHECK**: Match designs pixel-close where specified; use shadcn/ui primitives otherwise for consistency
- **CHECK**: Suggest improvements rooted in accessibility or performance
- **REJECT**: Deviating from designs without approval
- **REJECT**: Implementing without clarifying ambiguities
- **REJECT**: Silently adopting green as a severity color because it "looks nice"

### 19.4 Working with Product Managers
- **RULE**: Clear communication on requirements and timelines
- **CHECK**: Clarify acceptance criteria before starting
- **CHECK**: Communicate blockers immediately
- **CHECK**: Provide realistic estimates including testing and accessibility work
- **CHECK**: Regular progress updates
- **CHECK**: Suggest technical alternatives when beneficial (e.g., "server-rendering this page saves 200ms and 80KB — can we skip the client-side filter for V1?")
- **REJECT**: Accepting vague requirements
- **REJECT**: Missing deadlines silently
- **REJECT**: Feature creep without sign-off

### 19.5 Daily Development Practices
- **RULE**: Be a productive team member
- **CHECK**: Attend standups prepared
- **CHECK**: Ticket status up-to-date
- **CHECK**: Unblock teammates proactively
- **CHECK**: Share learnings and gotchas (especially Next.js App Router quirks and TanStack Query patterns)
- **CHECK**: Document complex decisions in ADRs
- **CHECK**: Ask for help when stuck (max 2 hours before flagging)
- **REJECT**: Working in isolation
- **REJECT**: Hoarding knowledge
- **REJECT**: Not asking for help

---

## 🎓 DEVELOPER MINDSET

### When Building Features:

**Build with the user in mind.**
- Our users are lawyers reviewing privileged material under time pressure and liability exposure. They need speed, precision, and trust — in that order.
- Optimize for keyboard-first throughput, not first-time wow.
- Handle errors gracefully — no raw errors, no blank screens.
- Provide clear feedback on every action.

**Build with the team in mind.**
- Write self-documenting code
- Follow established patterns (shadcn/ui, TanStack Query, react-hook-form+zod)
- Create reusable components
- Make code easy to review

**Build with quality in mind.**
- Test thoroughly before submitting
- Follow SOLID principles
- Eliminate duplication
- Consider edge cases (empty queue, evaluator timeout, reviewer conflict-of-interest)

**Build with privacy in mind.**
- Every document is privileged. Act accordingly.
- If you wouldn't want it in a screenshot shared publicly, don't put it in a log, toast, analytics event, or URL.

### When Reviewing Code:
**Only change what is explicitly requested.**

Resist the temptation to "improve" code outside the request. Every unnecessary change adds risk and makes reviews harder.

**When in doubt:**
- ❓ Ask for clarification from PM/Designer/Backend
- 📖 Read existing code for established patterns
- 🔍 Search for similar implementations
- 💬 Discuss with the team
- 📚 Refer to this doc, the V1 PRD, and the architect rules
- 🚫 Don't assume or guess

### Time Management
- **Break down large features** into smaller tasks
- **Set realistic estimates** including accessibility and testing
- **Communicate delays early**
- **Timebox investigations** (max 2 hours)
- **Balance speed and quality** — in this product, "fast but broken" is a compliance event

---

## FINAL NOTE

These guidelines ensure you build high-quality, maintainable, performant, accessible, and privacy-respecting Next.js applications for CiteGuard. By following these standards, you will:

✅ **Deliver Features Faster**: Shared components, TanStack Query patterns, and App Router conventions accelerate work
✅ **Reduce Bugs**: Thorough testing, explicit states, and strict types catch issues early
✅ **Improve User Experience**: Accessibility, keyboard-first UX, and optimistic updates keep lawyers moving
✅ **Make Maintenance Easier**: Clean structure, shared patterns, and real docs help future you
✅ **Build Trust**: Consistent professionalism in UI and communication builds confidence with law-firm buyers
✅ **Protect Privilege**: No document content leaks via any client-side path — ever

**Remember**: Great frontend development here is not about delight animations or clever hacks. It's about creating an interface that a senior litigation partner would trust with a brief due tomorrow, and that an auditor would accept as evidence of diligent review. The bar is exactly that high.

### Key Principles to Internalize:
1. **SOLID principles** guide architecture decisions
2. **Server Components first**; Client Components deliberate
3. **TanStack Query** for server state; URL for shareable state; Zustand only when justified
4. **Zero code duplication** via shared components and hooks
5. **Performance** considered at every level
6. **Accessibility** is non-negotiable
7. **Professional tone** — no emoji, no gamification, no green
8. **Privacy**: privileged content never leaks through logs, URLs, analytics, or storage
9. **Testing** gives confidence
10. **Communication** keeps the team aligned

---

**Welcome to the CiteGuard Frontend Team! Let's build something that lawyers trust with the documents that keep them out of trouble.** 🚀