/** @type {import('next').NextConfig} */

// Backend URL for API rewrites - proxies /api/* requests to the backend
// In dev: defaults to localhost:8000
// In prod: set BACKEND_URL env var in Railway
// TEMPORARY HARDCODE FOR DEBUGGING - remove after confirming it works
const BACKEND_URL = process.env.BACKEND_URL || 'https://back-end-production-1219.up.railway.app';

// Log at build time so we can verify the value in Railway build logs
console.log(`[next.config.js] BACKEND_URL at build time: ${BACKEND_URL}`);

// Include localhost in CSP only during development
// In production, we only need the railway.app domains
const isDev = process.env.NODE_ENV !== 'production';
const localhostCsp = isDev ? ' http://localhost:8000' : '';

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
      `connect-src 'self' https://*.railway.app https://*.up.railway.app${localhostCsp}`,
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
  // Proxy API requests to backend - this is the CORRECT way to handle API routing
  // Frontend uses relative /api/* URLs, Next.js proxies them to BACKEND_URL
  // No need for NEXT_PUBLIC_API_URL build-time variable!
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/health',
        destination: `${BACKEND_URL}/health`,
      },
    ];
  },
};

module.exports = nextConfig;
