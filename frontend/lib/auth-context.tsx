'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://back-end-production-1219.up.railway.app/api';

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
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'cocktail_auth_token';
const USER_KEY = 'cocktail_auth_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user with token
  // Returns: { user, shouldClearAuth }
  // shouldClearAuth is true only for definitive auth failures (401), not network errors
  const fetchCurrentUser = useCallback(async (authToken: string): Promise<{ user: User | null; shouldClearAuth: boolean }> => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });
      if (res.ok) {
        const userData = await res.json();
        return { user: userData, shouldClearAuth: false };
      }
      // 401/403 = token is definitely invalid, clear it
      if (res.status === 401 || res.status === 403) {
        return { user: null, shouldClearAuth: true };
      }
      // Other errors (500, etc) - don't clear auth, might be temporary
      return { user: null, shouldClearAuth: false };
    } catch {
      // Network error (offline) - don't clear auth
      return { user: null, shouldClearAuth: false };
    }
  }, []);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUserJson = localStorage.getItem(USER_KEY);

      if (storedToken) {
        // First, restore from cache immediately (for offline support)
        let cachedUser: User | null = null;
        if (storedUserJson) {
          try {
            cachedUser = JSON.parse(storedUserJson);
          } catch {
            // Invalid JSON, ignore
          }
        }

        // If online, validate token with server
        if (navigator.onLine) {
          const { user: freshUser, shouldClearAuth } = await fetchCurrentUser(storedToken);
          if (freshUser) {
            // Token valid, update cache
            setToken(storedToken);
            setUser(freshUser);
            localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
          } else if (shouldClearAuth) {
            // Token definitely invalid (401/403), clear everything
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
          } else if (cachedUser) {
            // Network/server error but we have cached user - use it
            setToken(storedToken);
            setUser(cachedUser);
          }
        } else if (cachedUser) {
          // Offline - use cached credentials
          setToken(storedToken);
          setUser(cachedUser);
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, [fetchCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await res.json();
    const newToken = data.access_token;

    // Store token
    localStorage.setItem(TOKEN_KEY, newToken);
    setToken(newToken);

    // Fetch user info
    const { user: currentUser } = await fetchCurrentUser(newToken);
    if (currentUser) {
      setUser(currentUser);
      // Cache user data for offline access
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
    }
  }, [fetchCurrentUser]);

  const register = useCallback(async (email: string, password: string, displayName?: string) => {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
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

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
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
