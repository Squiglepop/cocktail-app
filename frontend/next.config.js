/** @type {import('next').NextConfig} */

// Backend API URL - MUST be set in production
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  // Enable standalone output for optimized Docker builds
  output: 'standalone',

  async rewrites() {
    console.log('BACKEND_URL:', BACKEND_URL);
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
