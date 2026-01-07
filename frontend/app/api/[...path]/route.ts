/**
 * Runtime API Proxy - Catch-all route for /api/* requests
 *
 * This replaces Next.js rewrites() which evaluates at build time.
 * BACKEND_URL is read at runtime (per-request), so Railway env vars work properly.
 *
 * Key features:
 * - Forwards all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS)
 * - Preserves cookies (critical for httpOnly refresh tokens)
 * - Forwards Authorization headers (Bearer tokens)
 * - Handles multipart/form-data for file uploads
 * - Returns 502 if backend unreachable
 */

import { NextRequest, NextResponse } from 'next/server';

// Runtime config - read at request time, not build time
function getBackendUrl(): string {
  // BACKEND_URL env var is checked at runtime
  // Falls back to production URL or localhost based on environment
  return (
    process.env.BACKEND_URL ||
    (process.env.NODE_ENV === 'production'
      ? 'https://back-end-production-1219.up.railway.app'
      : 'http://localhost:8000')
  );
}

// Headers to NOT forward (hop-by-hop headers)
const EXCLUDED_REQUEST_HEADERS = new Set([
  'host',
  'connection',
  'keep-alive',
  'transfer-encoding',
  'te',
  'trailer',
  'upgrade',
  'proxy-authorization',
  'proxy-connection',
]);

const EXCLUDED_RESPONSE_HEADERS = new Set([
  'transfer-encoding',
  'connection',
  'keep-alive',
]);

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[]
): Promise<NextResponse> {
  const backendUrl = getBackendUrl();
  const path = `/api/${pathSegments.join('/')}`;
  const url = new URL(path, backendUrl);

  // Preserve query string
  url.search = request.nextUrl.search;

  // Build headers to forward
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!EXCLUDED_REQUEST_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  // Forward cookies (critical for httpOnly refresh tokens)
  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) {
    headers.set('cookie', cookieHeader);
  }

  // Forward Authorization header (Bearer tokens)
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.set('authorization', authHeader);
  }

  // Prepare request options
  const fetchOptions: RequestInit = {
    method: request.method,
    headers,
    // Prevent fetch from following redirects - let client handle them
    redirect: 'manual',
  };

  // Handle request body for non-GET/HEAD methods
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    const contentType = request.headers.get('content-type') || '';

    if (contentType.includes('multipart/form-data')) {
      // For file uploads, forward the raw body as-is
      // The boundary is already in the content-type header
      fetchOptions.body = await request.arrayBuffer();
    } else if (contentType.includes('application/json')) {
      // JSON body
      fetchOptions.body = await request.text();
    } else if (contentType.includes('application/x-www-form-urlencoded')) {
      // Form data
      fetchOptions.body = await request.text();
    } else if (request.body) {
      // Other body types - forward as-is
      fetchOptions.body = await request.arrayBuffer();
    }
  }

  try {
    const response = await fetch(url.toString(), fetchOptions);

    // Build response headers, including Set-Cookie for auth
    const responseHeaders = new Headers();
    response.headers.forEach((value, key) => {
      if (!EXCLUDED_RESPONSE_HEADERS.has(key.toLowerCase())) {
        // Handle multiple Set-Cookie headers properly
        if (key.toLowerCase() === 'set-cookie') {
          // Append each Set-Cookie header individually
          responseHeaders.append(key, value);
        } else {
          responseHeaders.set(key, value);
        }
      }
    });

    // Get response body
    const body = await response.arrayBuffer();

    return new NextResponse(body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[API Proxy] Backend request failed:', error);
    return NextResponse.json(
      { detail: 'Backend service unavailable' },
      { status: 502 }
    );
  }
}

// Export handlers for all HTTP methods
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}

// Handle OPTIONS for CORS preflight
export async function OPTIONS(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return proxyRequest(request, path);
}
