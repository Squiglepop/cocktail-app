import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ServiceWorkerRegistration } from '@/components/ServiceWorkerRegistration';
import { Header } from '@/components/Header';
import { AuthProvider } from '@/lib/auth-context';
import { FavouritesProvider } from '@/lib/favourites-context';
import { QueryProvider } from '@/lib/query-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Cocktail Recipe Library',
  description: 'Extract and manage cocktail recipes from screenshots',
  manifest: '/manifest.json',
  appleWebApp: {
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
        <meta name="mobile-web-app-capable" content="yes" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
      </head>
      <body className={inter.className}>
        <QueryProvider>
          <AuthProvider>
            <FavouritesProvider>
              <ServiceWorkerRegistration />
              <div className="min-h-screen flex flex-col">
                <Header />
                <main className="flex-1">{children}</main>
                <footer className="border-t border-gray-200 bg-white py-6">
                  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <p className="text-center text-gray-500 text-sm">
                      Cocktail Recipe Library - Extract recipes from screenshots using AI
                    </p>
                  </div>
                </footer>
              </div>
            </FavouritesProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
