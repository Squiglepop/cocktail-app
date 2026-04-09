'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { useDuplicateDetection, useMergeIngredients } from '@/lib/hooks';
import { IngredientDuplicateGroup, formatEnumValue } from '@/lib/api';
import { MergePreviewModal } from './MergePreviewModal';

interface DuplicateDetectionPanelProps {
  token: string | null;
}

function formatDetectionReason(reason: string, score: number): string {
  switch (reason) {
    case 'exact_match_case_insensitive': return 'Exact Match';
    case 'fuzzy_match': return `Fuzzy Match (${Math.round(score * 100)}%)`;
    case 'variation_pattern': return 'Variation Pattern';
    default: return reason;
  }
}

export function DuplicateDetectionPanel({ token }: DuplicateDetectionPanelProps) {
  const [showDuplicates, setShowDuplicates] = useState(false);
  const [mergingGroup, setMergingGroup] = useState<IngredientDuplicateGroup | null>(null);
  const [mergeMessage, setMergeMessage] = useState<string | null>(null);

  const { data, isLoading, error } = useDuplicateDetection(token, showDuplicates);
  const mergeMutation = useMergeIngredients();

  const handleMerge = () => {
    if (!mergingGroup) return;
    mergeMutation.mutate(
      {
        data: {
          target_id: mergingGroup.target.ingredient_id,
          source_ids: mergingGroup.duplicates.map((d) => d.ingredient_id),
        },
        token,
      },
      {
        onSuccess: (result) => {
          setMergingGroup(null);
          setMergeMessage(
            `Merged: ${result.recipes_affected} recipes updated, ${result.sources_removed} ingredients removed`
          );
        },
        onError: () => {
          setMergingGroup(null);
          setMergeMessage('Failed to merge ingredients');
        },
      }
    );
  };

  return (
    <div className="mt-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Duplicate Detection</h2>
        <button
          onClick={() => setShowDuplicates(true)}
          disabled={isLoading}
          className="btn bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              Scanning...
            </>
          ) : (
            'Show Duplicates'
          )}
        </button>
      </div>

      {mergeMessage && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-700 text-sm flex justify-between items-center">
          <span>{mergeMessage}</span>
          <button onClick={() => setMergeMessage(null)} className="text-green-500 hover:text-green-700 font-medium">Dismiss</button>
        </div>
      )}

      {error && showDuplicates && (
        <div className="text-center py-8 text-red-600">
          Error loading duplicate detection results.
        </div>
      )}

      {data && showDuplicates && (
        <>
          {data.groups.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No duplicates detected
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-500 mb-4">
                Found {data.total_groups} {data.total_groups === 1 ? 'group' : 'groups'} with {data.total_duplicates} potential {data.total_duplicates === 1 ? 'duplicate' : 'duplicates'}
              </p>

              <div className="space-y-4">
                {data.groups.map((group, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4">
                    {/* Target */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="inline-block px-2 py-0.5 bg-green-100 text-green-800 text-xs font-medium rounded">
                          suggested target
                        </span>
                        <span className="font-medium">{group.target.name}</span>
                        <span className="text-sm text-gray-500">
                          {formatEnumValue(group.target.type)} &middot; {group.target.usage_count} recipes
                        </span>
                      </div>
                      <button
                        onClick={() => setMergingGroup(group)}
                        className="btn bg-amber-600 text-white hover:bg-amber-700 text-sm"
                      >
                        Merge
                      </button>
                    </div>

                    {/* Duplicates */}
                    {group.duplicates.map((dup) => (
                      <div key={dup.ingredient_id} className="flex items-center gap-2 ml-4 py-1">
                        <span className="text-gray-700">{dup.name}</span>
                        <span className="text-sm text-gray-500">{formatEnumValue(dup.type)}</span>
                        <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                          {formatDetectionReason(dup.detection_reason, dup.similarity_score)}
                        </span>
                        <span className="text-sm text-gray-400">{dup.usage_count} recipes</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}

      {/* Merge Preview Modal */}
      {mergingGroup && (
        <MergePreviewModal
          isOpen={true}
          group={mergingGroup}
          onConfirm={handleMerge}
          onCancel={() => setMergingGroup(null)}
          isMerging={mergeMutation.isPending}
        />
      )}
    </div>
  );
}
