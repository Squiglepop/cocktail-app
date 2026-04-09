'use client';

import { useEffect } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { IngredientDuplicateGroup, formatEnumValue } from '@/lib/api';

interface MergePreviewModalProps {
  isOpen: boolean;
  group: IngredientDuplicateGroup;
  onConfirm: () => void;
  onCancel: () => void;
  isMerging: boolean;
}

export function MergePreviewModal({
  isOpen,
  group,
  onConfirm,
  onCancel,
  isMerging,
}: MergePreviewModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const affectedRecipes = group.duplicates.reduce((sum, d) => sum + d.usage_count, 0);

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
            <AlertTriangle className="h-5 w-5 text-amber-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Merge Ingredients</h2>
        </div>

        {/* Target */}
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-500 mb-1">Keep (target):</p>
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <span className="font-medium text-green-800">{group.target.name}</span>
            <span className="text-sm text-green-600 ml-2">({formatEnumValue(group.target.type)}, {group.target.usage_count} recipes)</span>
          </div>
        </div>

        {/* Sources */}
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-500 mb-1">Merge and remove:</p>
          {group.duplicates.map((dup) => (
            <div key={dup.ingredient_id} className="p-3 bg-red-50 border border-red-200 rounded-md mb-2">
              <span className="font-medium text-red-800">{dup.name}</span>
              <span className="text-sm text-red-600 ml-2">({formatEnumValue(dup.type)}, {dup.usage_count} recipes)</span>
            </div>
          ))}
        </div>

        {/* Warning */}
        <div className="mb-6 p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
          This will update all recipes using the source ingredients to use &apos;{group.target.name}&apos; instead.
          Source ingredients will be deleted. <strong>{affectedRecipes} recipes</strong> will be affected.
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isMerging}
            className="btn btn-secondary"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isMerging}
            className="btn bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
          >
            {isMerging ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Merging...
              </>
            ) : (
              'Confirm Merge'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
