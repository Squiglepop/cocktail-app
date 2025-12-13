/**
 * Web Share API utilities for sharing recipes with images
 */

import { getRecipeImageUrl } from './api';

interface ShareRecipeOptions {
  id: string;
  name: string;
  hasImage: boolean;
}

/**
 * Fetches recipe image and converts to a File object for sharing
 */
async function fetchImageAsFile(recipeId: string, recipeName: string): Promise<File | null> {
  try {
    const imageUrl = getRecipeImageUrl(recipeId);
    const response = await fetch(imageUrl);

    if (!response.ok) return null;

    const blob = await response.blob();
    const fileName = `${recipeName.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.jpg`;

    return new File([blob], fileName, { type: blob.type || 'image/jpeg' });
  } catch (error) {
    console.error('Failed to fetch image for sharing:', error);
    return null;
  }
}

/**
 * Check if the browser supports sharing files
 */
function canShareFiles(): boolean {
  return typeof navigator !== 'undefined' &&
         'canShare' in navigator &&
         navigator.canShare({ files: [new File([''], 'test.txt', { type: 'text/plain' })] });
}

/**
 * Share a recipe using the Web Share API
 * Includes the recipe thumbnail if available and supported
 */
export async function shareRecipe(recipe: ShareRecipeOptions): Promise<boolean> {
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
  const recipeUrl = `${baseUrl}/recipes/${recipe.id}`;

  const shareData: ShareData = {
    title: recipe.name,
    text: `Check out this ${recipe.name} cocktail recipe!`,
    url: recipeUrl,
  };

  // Check if Web Share API is available
  if (typeof navigator === 'undefined' || !navigator.share) {
    // Fallback: copy link to clipboard
    await copyToClipboard(recipeUrl);
    return false;
  }

  try {
    // Try to include image if available and browser supports file sharing
    if (recipe.hasImage && canShareFiles()) {
      const imageFile = await fetchImageAsFile(recipe.id, recipe.name);

      if (imageFile && navigator.canShare({ files: [imageFile] })) {
        shareData.files = [imageFile];
      }
    }

    await navigator.share(shareData);
    return true;
  } catch (error) {
    // User cancelled or share failed
    if ((error as Error).name !== 'AbortError') {
      console.error('Share failed:', error);
      // Fallback to clipboard
      await copyToClipboard(recipeUrl);
    }
    return false;
  }
}

/**
 * Copy text to clipboard with fallback
 */
async function copyToClipboard(text: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text);
    // Could trigger a toast notification here
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
  }
}

/**
 * Check if Web Share API is available
 */
export function isShareSupported(): boolean {
  return typeof navigator !== 'undefined' && 'share' in navigator;
}
