# Frontend - Utah Cannabis Aggregator

Next.js-based frontend for the Utah Cannabis Aggregator platform. Built with React, TypeScript, and Tailwind CSS for optimal SEO and mobile performance.

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your API URL and Supabase credentials
```

3. Run development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/                 # Next.js App Router
│   ├── layout.tsx       # Root layout component (wrapped in Providers)
│   ├── providers.tsx    # Client-side providers (AuthProvider)
│   ├── page.tsx         # Home page
│   └── globals.css      # Global styles
├── components/          # Reusable React components
├── lib/                 # Utility functions and API client
│   ├── api.ts           # Axios API client
│   ├── AuthContext.tsx  # Global auth context with useAuth() hook
│   └── supabase.ts      # Supabase client configuration
├── public/              # Static assets
├── tailwind.config.ts   # Tailwind CSS configuration
├── tsconfig.json        # TypeScript configuration
├── next.config.js       # Next.js configuration
├── package.json         # Dependencies
└── README.md            # This file
```

## Key Features

- **Server-Side Rendering (SSR)**: Optimized for SEO with Next.js App Router
- **TypeScript**: Full type safety for better development experience
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Responsive Design**: Mobile-first approach (important for dispensary browsing)
- **API Integration**: Axios client pre-configured for backend communication

## Available Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run ESLint
npm run lint

# Type checking
npm run type-check
```

## Environment Variables

See `.env.example` for available configuration options.

Key variables:
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anonymous key

## Component Structure (Planned)

- `Header.tsx` - Navigation and branding
- `Footer.tsx` - Footer with compliance notice
- `ProductCard.tsx` - Product display card
- `PriceComparison.tsx` - Price comparison view
- `ReviewsList.tsx` - Product reviews section
- `SearchBar.tsx` - Product search interface
- `FilterPanel.tsx` - Search filters

## Pages (Planned)

- `/` - Home page
- `/products` - Product browse/search
- `/products/[id]` - Product details with prices and reviews
- `/auth/login` - User login
- `/auth/register` - User registration
- `/profile` - User profile and reviews

## Styling

This project uses **Tailwind CSS** for styling. A custom cannabis-themed color palette has been configured:

```
cannabis-50: #f5fdf0   (lightest)
cannabis-500: #52c952  (primary)
cannabis-900: #1f4620  (darkest)
```

All styles are utility-based for consistency and rapid development.

## API Client

The `/lib/api.ts` file exports a pre-configured Axios instance with:
- Base URL pointing to the backend API
- Request/response interceptors for auth and error handling
- Typed API methods for all endpoints

Example usage:
```typescript
import { api } from '@/lib/api'

// Search products
const products = await api.products.search('Gorilla Glue')

// Compare prices
const prices = await api.prices.compare(productId)
```

## Authentication

Authentication is managed via a global React Context using Supabase Auth.

### AuthContext (`lib/AuthContext.tsx`)

The `AuthProvider` wraps the entire application and provides:
- `user` - Current Supabase User object (or null)
- `session` - Current Supabase Session (or null)
- `loading` - Boolean indicating if auth state is being fetched
- `signOut()` - Function to sign out the user

### Using Authentication in Components

```typescript
import { useAuth } from '@/lib/AuthContext'

export function MyComponent() {
  const { user, session, loading, signOut } = useAuth()

  if (loading) return <div>Loading...</div>

  if (!user) {
    return <div>Please sign in to continue</div>
  }

  return (
    <div>
      <p>Welcome, {user.email}</p>
      <button onClick={signOut}>Sign Out</button>
    </div>
  )
}
```

### Important Notes

- **Always use `useAuth()`** instead of making direct Supabase auth calls in components
- The AuthContext automatically syncs auth state across all components
- Auth state persists correctly across page reloads and tab switches
- The context listens to `onAuthStateChange` events for real-time updates

## Performance Considerations

1. **SEO Optimization**: Next.js metadata API for dynamic meta tags
2. **Mobile Responsiveness**: 80% of users will access via mobile
3. **Load Time**: Target <200ms for search results
4. **Image Optimization**: Use Next.js Image component for all images
5. **Code Splitting**: Lazy load components when possible

## Development Workflow

1. Create feature branches for new features
2. Use TypeScript for type safety
3. Test responsive design on mobile devices
4. Ensure compliance messaging is always visible
5. Run `npm run type-check` before committing

## Deployment

This frontend is designed to be deployed on **Vercel**:

1. Connect your repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on every push to main

## Testing (To Be Implemented)

- Jest for unit tests
- React Testing Library for component tests
- Playwright for E2E tests

## Next Steps

1. Create page components for products, search, and details
2. Build product browsing UI
3. Implement client-side filtering
4. Add user authentication pages
5. Create review submission forms
