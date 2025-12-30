/** @type {import('next').NextConfig} */

// Security headers for all routes
const securityHeaders = [
  {
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Next.js requires these
      "style-src 'self' 'unsafe-inline'", // Tailwind uses inline styles
      "img-src 'self' data: blob: https:",
      "font-src 'self'",
      "connect-src 'self' https://*.railway.app https://*.up.railway.app http://localhost:8000",
      "frame-ancestors 'self'", // Allow self for hidden iframe warmup
      "base-uri 'self'",
      "form-action 'self'",
    ].join('; ')
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-Frame-Options',
    value: 'SAMEORIGIN' // Allow self for hidden iframe warmup
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin'
  },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()'
  }
];

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
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/:path*',
        headers: securityHeaders,
      },
    ];
  },
};

module.exports = nextConfig;
