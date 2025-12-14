/** @type {import('next').NextConfig} */

const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/recipes/**',
      },
      {
        protocol: 'https',
        hostname: '*.railway.app',
        pathname: '/api/recipes/**',
      },
      {
        protocol: 'https',
        hostname: '*.up.railway.app',
        pathname: '/api/recipes/**',
      },
    ],
  },
};

module.exports = nextConfig;
