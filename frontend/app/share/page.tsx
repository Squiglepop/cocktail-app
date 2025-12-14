'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { uploadAndExtract, Recipe } from '@/lib/api';
import { Loader2, CheckCircle, AlertCircle, Wine } from 'lucide-react';
import Link from 'next/link';

function ShareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'waiting' | 'processing' | 'success' | 'error'>('waiting');
  const [error, setError] = useState<string | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);

  useEffect(() => {
    // Listen for shared images from service worker
    const handleMessage = async (event: MessageEvent) => {
      if (event.data?.type === 'SHARED_IMAGE' && event.data.image) {
        setStatus('processing');
        try {
          const file = event.data.image as File;
          const extractedRecipe = await uploadAndExtract(file);
          setRecipe(extractedRecipe);
          setStatus('success');
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to extract recipe');
          setStatus('error');
        }
      } else if (event.data?.type === 'NO_SHARED_IMAGE') {
        setError('No image was received. Please try sharing again.');
        setStatus('error');
      }
    };

    navigator.serviceWorker?.addEventListener('message', handleMessage);

    // If we were redirected here after receiving a share, request the image from SW
    if (searchParams.get('received') === 'true') {
      // Wait for service worker to be ready, then request the shared image
      navigator.serviceWorker?.ready.then((registration) => {
        registration.active?.postMessage({ type: 'GET_SHARED_IMAGE' });
      });
    }

    return () => {
      navigator.serviceWorker?.removeEventListener('message', handleMessage);
    };
  }, [searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {status === 'waiting' && (
          <div className="card p-8 text-center">
            <div className="p-4 bg-amber-100 rounded-full w-fit mx-auto mb-4">
              <Wine className="h-12 w-12 text-amber-600" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Receiving Image...
            </h1>
            <p className="text-gray-500 mb-4">
              Waiting for the shared image to arrive
            </p>
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-amber-600" />
            <p className="text-sm text-gray-400 mt-4">
              If nothing happens, try sharing the image again or{' '}
              <Link href="/upload" className="text-amber-600 hover:underline">
                upload manually
              </Link>
            </p>
          </div>
        )}

        {status === 'processing' && (
          <div className="card p-8 text-center">
            <div className="p-4 bg-amber-100 rounded-full w-fit mx-auto mb-4">
              <Loader2 className="h-12 w-12 text-amber-600 animate-spin" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Extracting Recipe...
            </h1>
            <p className="text-gray-500">
              Our AI is analyzing the image to extract the cocktail recipe
            </p>
          </div>
        )}

        {status === 'success' && recipe && (
          <div className="card p-8 text-center">
            <div className="p-4 bg-green-100 rounded-full w-fit mx-auto mb-4">
              <CheckCircle className="h-12 w-12 text-green-600" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Recipe Extracted!
            </h1>
            <p className="text-gray-600 mb-6">
              <strong>{recipe.name}</strong> has been added to your collection
            </p>
            <div className="space-y-3">
              <Link
                href={`/recipes/${recipe.id}`}
                className="btn btn-primary w-full justify-center"
              >
                View Recipe
              </Link>
              <Link
                href={`/upload?enhance=${recipe.id}`}
                className="btn btn-secondary w-full justify-center"
              >
                Add More Images
              </Link>
              <Link
                href="/recipes"
                className="btn btn-ghost w-full justify-center text-gray-500"
              >
                Browse All Recipes
              </Link>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="card p-8 text-center">
            <div className="p-4 bg-red-100 rounded-full w-fit mx-auto mb-4">
              <AlertCircle className="h-12 w-12 text-red-600" />
            </div>
            <h1 className="text-xl font-semibold text-gray-900 mb-2">
              Extraction Failed
            </h1>
            <p className="text-red-600 mb-6">{error}</p>
            <div className="space-y-3">
              <Link
                href="/upload"
                className="btn btn-primary w-full justify-center"
              >
                Try Manual Upload
              </Link>
              <button
                onClick={() => setStatus('waiting')}
                className="btn btn-secondary w-full justify-center"
              >
                Try Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SharePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
      </div>
    }>
      <ShareContent />
    </Suspense>
  );
}
