/** @type {import('next').NextConfig} */

// Backend API URL - defaults to local dev server
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  // Enable standalone output for optimized Docker builds
  output: 'standalone',

  async rewrites() {
    // Only use rewrites in development or when proxying to a separate backend
    // In production with same-origin backend, these won't be needed
    if (process.env.NEXT_PUBLIC_API_URL) {
      // If a full API URL is set, don't use rewrites (direct API calls)
      return [];
    }

    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${BACKEND_URL}/uploads/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
