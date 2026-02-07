# Context

## Key Files Modified

- `frontend/lib/api.ts` - Removed `signOut()` from the 401 response interceptor. This was THE KEY FIX. The interceptor was destroying the Supabase session whenever any API call returned 401, which happened during the initial auth flow before the backend JWT was obtained.
- `frontend/lib/supabase.ts` - Added explicit auth configuration: `autoRefreshToken: true`, `persistSession: true`, `storage: localStorage`, `detectSessionInUrl: true`. This ensures the Supabase client reliably persists and restores sessions.
- `frontend/lib/AuthContext.tsx` - Simplified to use only `onAuthStateChange` as the single source of truth for authentication state. Removed manual `getSession()` calls that could race with the event listener.
- `frontend/app/auth/callback/page.tsx` - Rewrote to use `useAuth()` hook instead of making direct Supabase calls. This ensures the callback page participates in the centralized auth flow rather than managing its own session state.
- `frontend/components/Navigation.tsx` - Added loading state handling so the navigation does not flash unauthenticated UI while auth state is being resolved.
- `frontend/components/ProtectedRoute.tsx` - Removed redundant `onAuthStateChange` listener that was duplicating the one in AuthContext and could cause conflicting state updates.
- `frontend/app/profile/page.tsx` - Changed to use the context-provided `signOut` function instead of calling `supabase.auth.signOut()` directly, ensuring consistent auth state cleanup.
- `frontend/components/UserNav.tsx` - Previously converted to use `useAuth()` hook (no changes needed in this fix).

## Decisions

- The 401 interceptor now only clears the stored backend JWT token, not the Supabase session. Token refresh and re-authentication are handled by the AuthContext.
- `onAuthStateChange` is the single authority for auth state. No component should call `getSession()` independently to determine logged-in status.
- All sign-out operations must go through the AuthContext `signOut` function to ensure consistent state cleanup across the application.

## Last Updated
2026-02-07
