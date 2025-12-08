import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link';
import { GlassWater, Upload } from 'lucide-react';
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Cocktail Recipe Library',
  description: 'Extract and manage cocktail recipes from screenshots',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Cocktails',
  },
};

export const viewport: Viewport = {
  themeColor: '#d97706',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="apple-touch-icon" href="/icons/icon-192.svg" />
      </head>
      <body className={inter.className}>
        <ServiceWorkerRegistration />
        <div className="min-h-screen flex flex-col">
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
                  <Link
                    href="/"
                    className="text-gray-600 hover:text-gray-900 font-medium"
                  >
                    Recipes
                  </Link>
                  <Link
                    href="/upload"
                    className="btn btn-primary flex items-center gap-2"
                  >
                    <Upload className="h-4 w-4" />
                    Upload
                  </Link>
                </nav>
              </div>
            </div>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="border-t border-gray-200 bg-white py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <p className="text-center text-gray-500 text-sm">
                Cocktail Recipe Library - Extract recipes from screenshots using AI
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
