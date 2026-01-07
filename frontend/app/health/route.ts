/**
 * Health endpoint proxy for offline detection
 *
 * Proxies /health to the backend health endpoint.
 * Returns 502 if backend is down (triggers offline mode in frontend).
 */

import { NextRequest, NextResponse } from 'next/server';

function getBackendUrl(): string {
  return (
    process.env.BACKEND_URL ||
    (process.env.NODE_ENV === 'production'
      ? 'https://back-end-production-1219.up.railway.app'
      : 'http://localhost:8000')
  );
}

export async function GET(request: NextRequest) {
  const backendUrl = getBackendUrl();
  const url = new URL('/health', backendUrl);

  // Preserve query string (cache-busting param)
  url.search = request.nextUrl.search;

  try {
    const response = await fetch(url.toString(), {
      method: 'GET',
      cache: 'no-store',
    });

    const body = await response.text();

    return new NextResponse(body, {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') || 'application/json',
        'cache-control': 'no-store, no-cache, must-revalidate',
      },
    });
  } catch (error) {
    console.error('[Health Proxy] Backend unavailable:', error);
    return NextResponse.json(
      { status: 'error', detail: 'Backend unavailable' },
      { status: 502 }
    );
  }
}
