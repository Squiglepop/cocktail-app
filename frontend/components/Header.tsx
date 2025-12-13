'use client';

import Link from 'next/link';
import { GlassWater, LogOut, User, ListMusic } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

export function Header() {
  const { user, isLoading, logout } = useAuth();

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center gap-2">
            <GlassWater className="h-8 w-8 text-amber-600" />
            <span className="text-xl font-bold text-gray-900">
              Cocktail Library
            </span>
          </Link>
          <nav className="flex items-center gap-4">
            {/* Auth UI */}
            {isLoading ? (
              <div className="w-20 h-8 bg-gray-100 rounded animate-pulse" />
            ) : user ? (
              <div className="flex items-center gap-4">
                <Link
                  href="/playlists"
                  className="flex items-center gap-1 text-gray-600 hover:text-amber-600 text-sm font-medium"
                  title="My Playlists"
                >
                  <ListMusic className="h-4 w-4" />
                  <span className="hidden sm:inline">Playlists</span>
                </Link>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="h-4 w-4" />
                    <span className="hidden sm:inline">
                      {user.display_name || user.email}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center gap-1 text-gray-600 hover:text-gray-900 text-sm font-medium"
                    title="Logout"
                  >
                    <LogOut className="h-4 w-4" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-gray-600 hover:text-gray-900 text-sm font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  className="btn btn-secondary text-sm py-1.5 px-3"
                >
                  Register
                </Link>
              </div>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
