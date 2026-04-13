'use client';

import { useState, useEffect } from 'react';
import { Search, Plus, Pencil, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';
import {
  useAdminIngredients,
  useCreateIngredient,
  useUpdateIngredient,
  useDeleteIngredient,
} from '@/lib/hooks';
import { AdminIngredient, AdminIngredientCreate, AdminIngredientUpdate, formatEnumValue } from '@/lib/api';
import { IngredientFormModal } from '@/components/admin/IngredientFormModal';
import { ConfirmDeleteModal } from '@/components/ui/ConfirmDeleteModal';
import { DuplicateDetectionPanel } from '@/components/admin/DuplicateDetectionPanel';

const INGREDIENT_TYPES = [
  'spirit', 'liqueur', 'wine_fortified', 'bitter', 'syrup',
  'juice', 'mixer', 'dairy', 'egg', 'garnish', 'other',
] as const;

export default function IngredientsPage() {
  const { token } = useAuth();

  // State
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingIngredient, setEditingIngredient] = useState<AdminIngredient | null>(null);
  const [deletingIngredient, setDeletingIngredient] = useState<AdminIngredient | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  // Queries & mutations
  const { data, isLoading, error } = useAdminIngredients(
    { page, per_page: 50, search: debouncedSearch || undefined, type: typeFilter || undefined },
    token
  );
  const createMutation = useCreateIngredient();
  const updateMutation = useUpdateIngredient();
  const deleteMutation = useDeleteIngredient();

  const totalPages = data ? Math.ceil(data.total / 50) : 0;

  const handleCreate = (formData: AdminIngredientCreate | AdminIngredientUpdate) => {
    setFormError(null);
    createMutation.mutate(
      { data: formData as AdminIngredientCreate, token },
      {
        onSuccess: () => { setShowCreateForm(false); setFormError(null); },
        onError: (err) => { setFormError(err.message); },
      }
    );
  };

  const handleUpdate = (formData: AdminIngredientCreate | AdminIngredientUpdate) => {
    if (!editingIngredient) return;
    setFormError(null);
    updateMutation.mutate(
      { id: editingIngredient.id, data: formData as AdminIngredientUpdate, token },
      {
        onSuccess: () => { setEditingIngredient(null); setFormError(null); },
        onError: (err) => { setFormError(err.message); },
      }
    );
  };

  const handleDelete = () => {
    if (!deletingIngredient) return;
    deleteMutation.mutate(
      { id: deletingIngredient.id, token },
      {
        onSuccess: (result) => {
          setDeletingIngredient(null);
          if (!result.success) {
            setDeleteError(`Cannot delete: used in ${result.recipe_count} recipes`);
          }
        },
        onError: () => {
          setDeletingIngredient(null);
          setDeleteError('Failed to delete ingredient');
        },
      }
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ingredient Management</h1>
        <button
          onClick={() => { setShowCreateForm(true); setFormError(null); }}
          className="btn bg-amber-600 text-white hover:bg-amber-700 flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Ingredient
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search ingredients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <option value="">All Types</option>
          {INGREDIENT_TYPES.map((t) => (
            <option key={t} value={t}>{formatEnumValue(t)}</option>
          ))}
        </select>
      </div>

      {/* Delete error banner */}
      {deleteError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm flex justify-between items-center">
          <span>{deleteError}</span>
          <button onClick={() => setDeleteError(null)} className="text-red-500 hover:text-red-700 font-medium">Dismiss</button>
        </div>
      )}

      {/* Loading / Error / Table */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
        </div>
      )}

      {error && (
        <div className="text-center py-12 text-red-600">
          Error loading ingredients. Please try again.
        </div>
      )}

      {data && !isLoading && (
        <>
          <div className="text-sm text-gray-500 mb-2">
            Showing {data.items.length} of {data.total} ingredients
          </div>

          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Spirit Category</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data.items.map((ingredient) => (
                  <tr
                    key={ingredient.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => { setEditingIngredient(ingredient); setFormError(null); }}
                  >
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{ingredient.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">{formatEnumValue(ingredient.type)}</td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {ingredient.spirit_category ? formatEnumValue(ingredient.spirit_category) : '-'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => { e.stopPropagation(); setEditingIngredient(ingredient); setFormError(null); }}
                        className="text-gray-400 hover:text-amber-600 mr-2"
                        aria-label={`Edit ${ingredient.name}`}
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); setDeletingIngredient(ingredient); setDeleteError(null); }}
                        className="text-gray-400 hover:text-red-600"
                        aria-label={`Delete ${ingredient.name}`}
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                      No ingredients found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="btn btn-secondary flex items-center gap-1 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" /> Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="btn btn-secondary flex items-center gap-1 disabled:opacity-50"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}

      {/* Duplicate Detection Panel */}
      <DuplicateDetectionPanel token={token} />

      {/* Create Modal */}
      <IngredientFormModal
        isOpen={showCreateForm}
        ingredient={null}
        onClose={() => setShowCreateForm(false)}
        onSave={handleCreate}
        isSaving={createMutation.isPending}
        error={formError}
      />

      {/* Edit Modal */}
      <IngredientFormModal
        isOpen={editingIngredient !== null}
        ingredient={editingIngredient}
        onClose={() => setEditingIngredient(null)}
        onSave={handleUpdate}
        isSaving={updateMutation.isPending}
        error={formError}
      />

      {/* Delete Confirmation */}
      <ConfirmDeleteModal
        isOpen={deletingIngredient !== null}
        title="Delete Ingredient"
        itemName={deletingIngredient?.name || ''}
        onConfirm={handleDelete}
        onCancel={() => setDeletingIngredient(null)}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
