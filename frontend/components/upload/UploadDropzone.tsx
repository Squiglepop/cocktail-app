'use client';

import { useCallback, useState, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image, Loader2, CheckCircle, AlertCircle, Link, Clipboard, Plus, AlertTriangle } from 'lucide-react';
import { uploadAndExtract, enhanceRecipeWithImages, checkForDuplicates, Recipe, DuplicateMatch } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { cn } from '@/lib/utils';

interface UploadDropzoneProps {
  onRecipeExtracted: (recipe: Recipe) => void;
  /** If provided, enhance this recipe instead of creating new */
  enhanceRecipeId?: string;
  /** Callback when enhancement completes */
  onEnhanceComplete?: (recipe: Recipe) => void;
}

type UploadState = 'idle' | 'checking' | 'duplicate_warning' | 'uploading' | 'success' | 'error';
type InputMode = 'drop' | 'url';

export function UploadDropzone({
  onRecipeExtracted,
  enhanceRecipeId,
  onEnhanceComplete
}: UploadDropzoneProps) {
  const { token } = useAuth();
  const [state, setState] = useState<UploadState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [inputMode, setInputMode] = useState<InputMode>('drop');
  const [imageUrl, setImageUrl] = useState('');
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [duplicateMatches, setDuplicateMatches] = useState<DuplicateMatch[]>([]);
  const urlInputRef = useRef<HTMLInputElement>(null);

  const isEnhanceMode = !!enhanceRecipeId;

  const doExtraction = useCallback(async (files: File[]) => {
    setState('uploading');
    setError(null);

    try {
      if (isEnhanceMode && enhanceRecipeId) {
        // Enhancement mode - add all files to existing recipe
        const recipe = await enhanceRecipeWithImages(enhanceRecipeId, files, token);
        setState('success');
        onEnhanceComplete?.(recipe);
      } else {
        // Normal mode - create new recipe from all files
        const recipe = await uploadAndExtract(files, token);
        setState('success');
        onRecipeExtracted(recipe);
      }
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : isEnhanceMode ? 'Enhancement failed' : 'Upload failed');
    }
  }, [isEnhanceMode, enhanceRecipeId, token, onRecipeExtracted, onEnhanceComplete]);

  const processFiles = useCallback(async (files: File[]) => {
    if (files.length === 0) return;

    // Show preview of first file
    const reader = new FileReader();
    reader.onload = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(files[0]);

    setError(null);
    setPendingFiles(files);

    // Skip duplicate check in enhance mode
    if (isEnhanceMode) {
      await doExtraction(files);
      return;
    }

    // Check for duplicates first (only check first file)
    setState('checking');
    try {
      const duplicates = await checkForDuplicates(files[0], token);
      if (duplicates && duplicates.is_duplicate && duplicates.matches.length > 0) {
        // Show warning
        setDuplicateMatches(duplicates.matches);
        setState('duplicate_warning');
        return;
      }
    } catch {
      // Ignore duplicate check errors, proceed with upload
    }

    // No duplicates found, proceed with extraction
    await doExtraction(files);
  }, [isEnhanceMode, token, doExtraction]);

  const proceedWithUpload = useCallback(async () => {
    if (pendingFiles.length > 0) {
      await doExtraction(pendingFiles);
    }
  }, [pendingFiles, doExtraction]);

  const cancelUpload = useCallback(() => {
    setState('idle');
    setPendingFiles([]);
    setDuplicateMatches([]);
    setPreview(null);
  }, []);

  // Handle clipboard paste anywhere on the page
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      if (state === 'uploading') return;

      const items = e.clipboardData?.items;
      if (!items) return;

      const files: File[] = [];
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            files.push(file);
          }
        }
      }

      if (files.length > 0) {
        e.preventDefault();
        await processFiles(files);
      }
    };

    document.addEventListener('paste', handlePaste);
    return () => document.removeEventListener('paste', handlePaste);
  }, [state, processFiles]);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;
      await processFiles(acceptedFiles);
    },
    [processFiles]
  );

  const onDropRejected = useCallback((fileRejections: any[]) => {
    if (fileRejections.length > 0) {
      const rejection = fileRejections[0];
      const errorMessage = rejection.errors?.[0]?.message || 'File rejected';
      setError(errorMessage);
      setState('error');
    }
  }, []);

  const handleUrlSubmit = async () => {
    if (!imageUrl.trim()) return;

    setError(null);
    setPreview(imageUrl);

    try {
      // Fetch the image from URL
      const response = await fetch(imageUrl);
      if (!response.ok) throw new Error('Failed to fetch image');

      const blob = await response.blob();
      const file = new File([blob], 'image.jpg', { type: blob.type });

      await processFiles([file]);
    } catch (err) {
      setState('error');
      setError(err instanceof Error ? err.message : 'Failed to process URL');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    onDropRejected,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    },
    multiple: true,
    disabled: state === 'uploading' || state === 'checking' || state === 'duplicate_warning',
  });

  const reset = () => {
    setState('idle');
    setError(null);
    setPreview(null);
    setImageUrl('');
    setPendingFiles([]);
    setDuplicateMatches([]);
  };

  return (
    <div className="space-y-4">
      {/* Input mode toggle */}
      {state === 'idle' && (
        <div className="flex gap-2 justify-center">
          <button
            onClick={() => setInputMode('drop')}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              inputMode === 'drop'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <span className="flex items-center gap-2">
              <Clipboard className="h-4 w-4" />
              Drop / Paste
            </span>
          </button>
          <button
            onClick={() => {
              setInputMode('url');
              setTimeout(() => urlInputRef.current?.focus(), 100);
            }}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              inputMode === 'url'
                ? 'bg-amber-100 text-amber-800'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            )}
          >
            <span className="flex items-center gap-2">
              <Link className="h-4 w-4" />
              From URL
            </span>
          </button>
        </div>
      )}

      {/* Drop/Paste mode */}
      {inputMode === 'drop' && (
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            isDragActive && 'border-amber-500 bg-amber-50',
            state === 'idle' && 'border-gray-300 hover:border-amber-500 hover:bg-amber-50',
            state === 'uploading' && 'border-amber-500 bg-amber-50 cursor-wait',
            state === 'success' && 'border-green-500 bg-green-50',
            state === 'error' && 'border-red-500 bg-red-50'
          )}
        >
          <input {...getInputProps()} />

          {state === 'idle' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                {preview ? (
                  <img
                    src={preview}
                    alt="Preview"
                    className="max-h-48 rounded-lg"
                  />
                ) : (
                  <div className={cn("p-4 rounded-full", isEnhanceMode ? "bg-blue-100" : "bg-amber-100")}>
                    {isEnhanceMode ? (
                      <Plus className="h-12 w-12 text-blue-600" />
                    ) : (
                      <Image className="h-12 w-12 text-amber-600" />
                    )}
                  </div>
                )}
              </div>
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive
                    ? 'Drop your screenshot here'
                    : isEnhanceMode
                    ? 'Add more screenshots to this recipe'
                    : 'Upload a cocktail recipe screenshot'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  {isEnhanceMode
                    ? 'Add another image to enhance the recipe with more details'
                    : <>Drag and drop, click to select, or <strong>paste from clipboard (Cmd+V)</strong></>}
                </p>
              </div>
              <p className="text-xs text-gray-400">
                Supports JPG, PNG, GIF, WebP
              </p>
            </div>
          )}

          {state === 'checking' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex items-center justify-center gap-3">
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin" />
                <span className="text-lg font-medium text-gray-900">
                  Checking for duplicates...
                </span>
              </div>
            </div>
          )}

          {state === 'duplicate_warning' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex justify-center">
                <div className="p-4 bg-yellow-100 rounded-full">
                  <AlertTriangle className="h-12 w-12 text-yellow-600" />
                </div>
              </div>
              <div>
                <p className="text-lg font-medium text-yellow-800">
                  Possible duplicate detected
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  This image may already exist in your library:
                </p>
                <ul className="mt-2 space-y-1">
                  {duplicateMatches.slice(0, 3).map((match) => (
                    <li key={match.recipe_id} className="text-sm">
                      <a
                        href={`/recipes/${match.recipe_id}`}
                        className="text-amber-600 hover:underline font-medium"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {match.recipe_name}
                      </a>
                      <span className="text-gray-500 ml-2">
                        ({Math.round(match.confidence * 100)}% match)
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex gap-3 justify-center pt-2">
                <button
                  onClick={cancelUpload}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={proceedWithUpload}
                  className="btn btn-primary"
                >
                  Upload Anyway
                </button>
              </div>
            </div>
          )}

          {state === 'uploading' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex items-center justify-center gap-3">
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin" />
                <span className="text-lg font-medium text-gray-900">
                  {isEnhanceMode ? 'Enhancing recipe with AI...' : 'Extracting recipe with AI...'}
                </span>
              </div>
              <p className="text-sm text-gray-500">
                This may take a few seconds
              </p>
            </div>
          )}

          {state === 'success' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-green-100 rounded-full">
                  <CheckCircle className="h-12 w-12 text-green-600" />
                </div>
              </div>
              <p className="text-lg font-medium text-green-800">
                {isEnhanceMode ? 'Recipe enhanced successfully!' : 'Recipe extracted successfully!'}
              </p>
            </div>
          )}

          {state === 'error' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-red-100 rounded-full">
                  <AlertCircle className="h-12 w-12 text-red-600" />
                </div>
              </div>
              <p className="text-lg font-medium text-red-800">
                {isEnhanceMode ? 'Failed to enhance recipe' : 'Failed to extract recipe'}
              </p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* URL mode */}
      {inputMode === 'url' && state === 'idle' && (
        <div className="border-2 border-dashed rounded-lg p-8 border-gray-300">
          <div className="space-y-4">
            <div className="flex justify-center">
              <div className="p-4 bg-amber-100 rounded-full">
                <Link className="h-12 w-12 text-amber-600" />
              </div>
            </div>
            <div className="text-center">
              <p className="text-lg font-medium text-gray-900">
                Paste an image URL
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Enter a direct link to a cocktail recipe image
              </p>
            </div>
            <div className="flex gap-2">
              <input
                ref={urlInputRef}
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleUrlSubmit()}
                placeholder="https://example.com/recipe.jpg"
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
              <button
                onClick={handleUrlSubmit}
                disabled={!imageUrl.trim()}
                className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Extract
              </button>
            </div>
          </div>
        </div>
      )}

      {/* URL mode - loading/success/error states */}
      {inputMode === 'url' && state !== 'idle' && (
        <div
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center',
            (state === 'checking' || state === 'uploading') && 'border-amber-500 bg-amber-50',
            state === 'duplicate_warning' && 'border-yellow-500 bg-yellow-50',
            state === 'success' && 'border-green-500 bg-green-50',
            state === 'error' && 'border-red-500 bg-red-50'
          )}
        >
          {state === 'checking' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex items-center justify-center gap-3">
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin" />
                <span className="text-lg font-medium text-gray-900">
                  Checking for duplicates...
                </span>
              </div>
            </div>
          )}

          {state === 'duplicate_warning' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex justify-center">
                <div className="p-4 bg-yellow-100 rounded-full">
                  <AlertTriangle className="h-12 w-12 text-yellow-600" />
                </div>
              </div>
              <div>
                <p className="text-lg font-medium text-yellow-800">
                  Possible duplicate detected
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  This image may already exist in your library:
                </p>
                <ul className="mt-2 space-y-1">
                  {duplicateMatches.slice(0, 3).map((match) => (
                    <li key={match.recipe_id} className="text-sm">
                      <a
                        href={`/recipes/${match.recipe_id}`}
                        className="text-amber-600 hover:underline font-medium"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {match.recipe_name}
                      </a>
                      <span className="text-gray-500 ml-2">
                        ({Math.round(match.confidence * 100)}% match)
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="flex gap-3 justify-center pt-2">
                <button
                  onClick={cancelUpload}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={proceedWithUpload}
                  className="btn btn-primary"
                >
                  Upload Anyway
                </button>
              </div>
            </div>
          )}

          {state === 'uploading' && (
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  alt="Preview"
                  className="max-h-48 rounded-lg mx-auto opacity-75"
                />
              )}
              <div className="flex items-center justify-center gap-3">
                <Loader2 className="h-6 w-6 text-amber-600 animate-spin" />
                <span className="text-lg font-medium text-gray-900">
                  {isEnhanceMode ? 'Enhancing recipe with AI...' : 'Extracting recipe with AI...'}
                </span>
              </div>
              <p className="text-sm text-gray-500">
                This may take a few seconds
              </p>
            </div>
          )}

          {state === 'success' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-green-100 rounded-full">
                  <CheckCircle className="h-12 w-12 text-green-600" />
                </div>
              </div>
              <p className="text-lg font-medium text-green-800">
                {isEnhanceMode ? 'Recipe enhanced successfully!' : 'Recipe extracted successfully!'}
              </p>
            </div>
          )}

          {state === 'error' && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="p-4 bg-red-100 rounded-full">
                  <AlertCircle className="h-12 w-12 text-red-600" />
                </div>
              </div>
              <p className="text-lg font-medium text-red-800">
                {isEnhanceMode ? 'Failed to enhance recipe' : 'Failed to extract recipe'}
              </p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
        </div>
      )}

      {(state === 'success' || state === 'error') && (
        <div className="flex justify-center">
          <button onClick={reset} className="btn btn-secondary">
            {isEnhanceMode ? 'Add Another Image' : 'Upload Another'}
          </button>
        </div>
      )}
    </div>
  );
}
