# Auth State Synchronization Fix Plan

## Summary

Users were being logged out immediately after successful authentication. The root cause was the Axios 401 response interceptor in `frontend/lib/api.ts`, which called `signOut()` on every 401 response. This destroyed the Supabase session before it could be fully established, creating a race condition where authentication would appear to succeed but then immediately tear itself down.

## Approach

1. Remove the destructive `signOut()` call from the 401 interceptor so that receiving a 401 no longer wipes the session
2. Harden the Supabase client with explicit auth configuration (auto-refresh, persistence, storage)
3. Simplify AuthContext to rely solely on `onAuthStateChange` as the single source of truth for auth state
4. Rewrite the OAuth callback page to use the centralized `useAuth()` hook instead of making direct Supabase calls
5. Add loading state awareness to Navigation and clean up redundant listeners in ProtectedRoute
6. Ensure all components use context-provided `signOut` rather than calling Supabase directly

## Root Cause

The 401 interceptor was designed to handle expired tokens, but it fired during the initial authentication flow when the backend JWT had not yet been obtained. This caused `signOut()` to destroy the Supabase session, which in turn triggered `onAuthStateChange` with a `SIGNED_OUT` event, resetting all auth state across the application.
