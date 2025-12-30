'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode, useRef } from 'react';
import { API_BASE } from './api';

export interface User {
  id: string;
  email: string;
  display_name?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Access token stored in memory only (NOT localStorage) for XSS protection
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Prevent multiple refresh attempts simultaneously
  const isRefreshing = useRef(false);
  const refreshPromise = useRef<Promise<string | null> | null>(null);

  // Fetch current user with token
  const fetchCurrentUser = useCallback(async (authToken: string): Promise<User | null> => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
        // No credentials: 'include' needed - this endpoint uses Bearer token, not cookies
      });
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch {
      return null;
    }
  }, []);

  // Refresh access token using httpOnly cookie
  const refreshToken = useCallback(async (): Promise<string | null> => {
    // If already refreshing, return the existing promise
    if (isRefreshing.current && refreshPromise.current) {
      return refreshPromise.current;
    }

    isRefreshing.current = true;
    refreshPromise.current = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          credentials: 'include', // Send httpOnly cookie
        });

        if (res.ok) {
          const data = await res.json();
          const newToken = data.access_token;
          setToken(newToken);
          return newToken;
        }

        // Refresh failed (401) - user needs to log in again
        setToken(null);
        setUser(null);
        return null;
      } catch (error) {
        // Network error - return null to indicate refresh failed
        // Caller should handle gracefully (e.g., retry or prompt re-login)
        console.error('Token refresh failed:', error);
        return null;
      } finally {
        isRefreshing.current = false;
        refreshPromise.current = null;
      }
    })();

    return refreshPromise.current;
  }, []); // No dependencies - refresh token comes from httpOnly cookie, not state

  // Initialize auth state via silent refresh on page load
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Attempt silent refresh - if httpOnly cookie exists, we'll get a new token
        const newToken = await refreshToken();

        if (newToken) {
          // Token refreshed successfully, fetch user info
          const currentUser = await fetchCurrentUser(newToken);
          if (currentUser) {
            setUser(currentUser);
          }
        }
      } catch (error) {
        // Silent refresh failed - user is not authenticated
        console.error('Silent auth refresh failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []); // Empty deps - only run once on mount

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Receive httpOnly cookie
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await res.json();
    const newToken = data.access_token;

    // Store access token in memory only
    setToken(newToken);

    // Fetch user info
    const currentUser = await fetchCurrentUser(newToken);
    if (currentUser) {
      setUser(currentUser);
    }
  }, [fetchCurrentUser]);

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        email,
        password,
        display_name: displayName || null,
      }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail || 'Registration failed');
    }

    // Auto-login after registration
    await login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    try {
      // Call backend to clear httpOnly cookie
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch {
      // Logout failed on server, but still clear local state
    }

    // Clear local state regardless of server response
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Helper to get auth headers
export function getAuthHeaders(token: string | null): Record<string, string> {
  if (!token) return {};
  return { 'Authorization': `Bearer ${token}` };
}
