'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Recipe, formatEnumValue, formatUnit } from '@/lib/api';
import { UploadDropzone } from '@/components/upload/UploadDropzone';
import { ArrowRight, Wine, Clock, GlassWater } from 'lucide-react';

export default function UploadPage() {
  const router = useRouter();
  const [extractedRecipe, setExtractedRecipe] = useState<Recipe | null>(null);

  const handleRecipeExtracted = (recipe: Recipe) => {
    setExtractedRecipe(recipe);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Upload Recipe</h1>
        <p className="text-gray-500 mt-1">
          Upload a screenshot of a cocktail recipe and our AI will extract the
          details automatically.
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Upload area */}
        <div>
          <UploadDropzone onRecipeExtracted={handleRecipeExtracted} />
        </div>

        {/* Extracted recipe preview */}
        <div>
          {extractedRecipe ? (
            <div className="card p-6 space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {extractedRecipe.name}
                </h2>
                {extractedRecipe.description && (
                  <p className="text-gray-600 text-sm mt-1">
                    {extractedRecipe.description}
                  </p>
                )}
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                {extractedRecipe.template && (
                  <span className="badge badge-amber">
                    {formatEnumValue(extractedRecipe.template)}
                  </span>
                )}
                {extractedRecipe.main_spirit && (
                  <span className="badge badge-gray">
                    {formatEnumValue(extractedRecipe.main_spirit)}
                  </span>
                )}
              </div>

              {/* Meta info */}
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                {extractedRecipe.glassware && (
                  <div className="flex items-center gap-1">
                    <Wine className="h-4 w-4" />
                    {formatEnumValue(extractedRecipe.glassware)}
                  </div>
                )}
                {extractedRecipe.serving_style && (
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {formatEnumValue(extractedRecipe.serving_style)}
                  </div>
                )}
              </div>

              {/* Ingredients */}
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Ingredients</h3>
                {extractedRecipe.ingredients.length > 0 ? (
                  <ul className="space-y-1 text-sm">
                    {extractedRecipe.ingredients
                      .sort((a, b) => a.order - b.order)
                      .map((ri) => (
                        <li key={ri.id} className="text-gray-600">
                          {ri.amount && (
                            <>
                              {ri.amount} {formatUnit(ri.unit, ri.amount)}{' '}
                            </>
                          )}
                          {ri.ingredient.name}
                          {ri.notes && (
                            <span className="text-gray-400"> ({ri.notes})</span>
                          )}
                        </li>
                      ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">
                    No ingredients extracted
                  </p>
                )}
              </div>

              {/* Garnish */}
              {extractedRecipe.garnish && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-1">Garnish</h3>
                  <p className="text-sm text-gray-600">
                    {extractedRecipe.garnish}
                  </p>
                </div>
              )}

              {/* Actions */}
              <div className="pt-4 border-t border-gray-100">
                <Link
                  href={`/recipes/${extractedRecipe.id}`}
                  className="btn btn-primary w-full justify-center"
                >
                  View Full Recipe
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Link>
              </div>
            </div>
          ) : (
            <div className="card p-6 flex flex-col items-center justify-center h-full min-h-[300px] text-center">
              <GlassWater className="h-16 w-16 text-gray-200 mb-4" />
              <h3 className="font-medium text-gray-500">Extracted Recipe</h3>
              <p className="text-sm text-gray-400 mt-1">
                Upload a screenshot to see the extracted recipe here
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Ways to upload */}
      <div className="mt-12">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Ways to add recipes
        </h2>
        <div className="grid sm:grid-cols-4 gap-4 mb-8">
          <div className="card p-4 text-center">
            <div className="text-2xl mb-2">📋</div>
            <h3 className="font-medium text-gray-900 mb-1">Paste</h3>
            <p className="text-sm text-gray-600">
              Copy a screenshot and press Cmd+V / Ctrl+V
            </p>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl mb-2">📁</div>
            <h3 className="font-medium text-gray-900 mb-1">Drop</h3>
            <p className="text-sm text-gray-600">
              Drag and drop an image file onto the upload area
            </p>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl mb-2">🔗</div>
            <h3 className="font-medium text-gray-900 mb-1">URL</h3>
            <p className="text-sm text-gray-600">
              Paste a direct link to an image online
            </p>
          </div>
          <div className="card p-4 text-center">
            <div className="text-2xl mb-2">📱</div>
            <h3 className="font-medium text-gray-900 mb-1">Browse</h3>
            <p className="text-sm text-gray-600">
              Click to select a file from your device
            </p>
          </div>
        </div>

        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Tips for best results
        </h2>
        <div className="grid sm:grid-cols-3 gap-6">
          <div className="card p-4">
            <h3 className="font-medium text-gray-900 mb-2">Clear text</h3>
            <p className="text-sm text-gray-600">
              Make sure the recipe text is clearly visible and not obscured.
            </p>
          </div>
          <div className="card p-4">
            <h3 className="font-medium text-gray-900 mb-2">Full recipe</h3>
            <p className="text-sm text-gray-600">
              Include all ingredients and measurements in the screenshot.
            </p>
          </div>
          <div className="card p-4">
            <h3 className="font-medium text-gray-900 mb-2">Good quality</h3>
            <p className="text-sm text-gray-600">
              Higher resolution images produce better extraction results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
