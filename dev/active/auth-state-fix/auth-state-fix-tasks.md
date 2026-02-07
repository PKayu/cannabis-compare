# Tasks

## Root Cause Fix
- [x] Remove signOut() from 401 response interceptor in api.ts

## Auth Infrastructure Hardening
- [x] Add explicit auth config to Supabase client (autoRefreshToken, persistSession, storage, detectSessionInUrl)
- [x] Simplify AuthContext to use onAuthStateChange as the single source of truth

## Component Fixes
- [x] Rewrite callback page to use useAuth() instead of direct Supabase calls
- [x] Add loading state handling to Navigation component
- [x] Remove redundant onAuthStateChange listener from ProtectedRoute
- [x] Profile page uses context-provided signOut instead of direct Supabase signOut

## Status: COMPLETE

All tasks finished. Authentication sessions now persist correctly through the full login flow (magic link and OAuth). The 401 interceptor no longer destroys sessions, and all components use the centralized AuthContext for auth state.

## Last Updated
2026-02-07
