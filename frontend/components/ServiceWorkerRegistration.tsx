'use client';

import { useEffect } from 'react';
import { swDebug } from '@/lib/debug';

export function ServiceWorkerRegistration() {
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          swDebug.log('Service Worker registered:', registration.scope);
        })
        .catch((error) => {
          swDebug.error('Service Worker registration failed:', error);
        });
    }
  }, []);

  return null;
}
