'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useAdminCategories, useCreateCategory, useUpdateCategory, useDeleteCategory, useReorderCategories } from '@/lib/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-client';
import { AdminCategory } from '@/lib/api';
import { X, Plus, Pencil, Trash2, ChevronUp, ChevronDown, Loader2, Check, RotateCcw } from 'lucide-react';
import { clsx } from 'clsx';

interface CategoryManagementModalProps {
  isOpen: boolean;
  categoryType: string;
  categoryLabel: string;
  onClose: () => void;
}

const GLASSWARE_GROUPS = ['stemmed', 'short', 'tall', 'specialty'];

function toSnakeCase(label: string): string {
  return label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^[^a-z]+/, '').replace(/_$/, '');
}

export function CategoryManagementModal({
  isOpen,
  categoryType,
  categoryLabel,
  onClose,
}: CategoryManagementModalProps) {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const { data: categories, isLoading } = useAdminCategories(categoryType, token);
  const createMutation = useCreateCategory(categoryType);
  const updateMutation = useUpdateCategory(categoryType);
  const deleteMutation = useDeleteCategory(categoryType);
  const reorderMutation = useReorderCategories(categoryType);

  // Add form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newGlasswareCategory, setNewGlasswareCategory] = useState('stemmed');
  const [addError, setAddError] = useState('');

  // Inline edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const editInputRef = useRef<HTMLInputElement>(null);

  // Delete feedback state
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (editingId) {
          setEditingId(null);
          return;
        }
        handleClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, editingId]);

  // Focus edit input when editing starts
  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  const handleClose = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: queryKeys.categories.all });
    onClose();
  }, [queryClient, onClose]);

  const generatedValue = toSnakeCase(newLabel);
  const isValueInvalid = newLabel.trim().length > 0 && !generatedValue;

  const handleAdd = async () => {
    if (!newLabel.trim() || !generatedValue) return;
    setAddError('');
    const data: { value: string; label: string; description?: string; category?: string } = {
      value: generatedValue,
      label: newLabel.trim(),
    };
    if (newDescription.trim()) {
      data.description = newDescription.trim();
    }
    if (categoryType === 'glassware') {
      data.category = newGlasswareCategory;
    }
    try {
      await createMutation.mutateAsync({ data, token });
      setNewLabel('');
      setNewDescription('');
      setShowAddForm(false);
    } catch (err) {
      setAddError(err instanceof Error ? err.message : 'Failed to create category');
    }
  };

  const handleEditStart = (cat: AdminCategory) => {
    setEditingId(cat.id);
    setEditValue(cat.label);
  };

  const handleEditSave = async (id: string) => {
    if (!editValue.trim()) {
      setEditingId(null);
      return;
    }
    await updateMutation.mutateAsync({ id, data: { label: editValue.trim() }, token });
    setEditingId(null);
  };

  const handleEditKeyDown = (e: React.KeyboardEvent, id: string) => {
    if (e.key === 'Enter') {
      handleEditSave(id);
    } else if (e.key === 'Escape') {
      setEditingId(null);
    }
  };

  const handleDelete = async (cat: AdminCategory) => {
    try {
      const result = await deleteMutation.mutateAsync({ id: cat.id, token });
      setDeleteMessage(`${cat.value} deactivated. ${result.recipe_count} recipes affected.`);
      setTimeout(() => setDeleteMessage(null), 3000);
    } catch (err) {
      setDeleteMessage(err instanceof Error ? err.message : 'Failed to delete category');
      setTimeout(() => setDeleteMessage(null), 3000);
    }
  };

  const handleReactivate = async (cat: AdminCategory) => {
    setDeleteMessage(`Restoring ${cat.value}...`);
    try {
      const result = await updateMutation.mutateAsync({ id: cat.id, data: { is_active: true }, token });
      window.alert(`API response: ${JSON.stringify(result)}`);
      setDeleteMessage(`${cat.value} reactivated.`);
      setTimeout(() => setDeleteMessage(null), 3000);
    } catch (err) {
      window.alert(`API error: ${err instanceof Error ? err.message : JSON.stringify(err)}`);
      setDeleteMessage(`Failed to reactivate: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setTimeout(() => setDeleteMessage(null), 5000);
    }
  };

  const handleReorder = async (index: number, direction: 'up' | 'down') => {
    if (!categories) return;
    const newList = [...categories];
    const swapIndex = direction === 'up' ? index - 1 : index + 1;
    [newList[index], newList[swapIndex]] = [newList[swapIndex], newList[index]];
    const ids = newList.map(c => c.id);
    await reorderMutation.mutateAsync({ ids, token });
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[70] p-4"
      onClick={handleClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Manage {categoryLabel}
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Delete feedback */}
          {deleteMessage && (
            <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded text-sm text-amber-800">
              {deleteMessage}
            </div>
          )}

          {/* Add New button/form */}
          {!showAddForm ? (
            <button
              onClick={() => setShowAddForm(true)}
              className="mb-4 flex items-center gap-1 text-sm text-amber-600 hover:text-amber-700 font-medium"
            >
              <Plus className="h-4 w-4" />
              Add New
            </button>
          ) : (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg space-y-2">
              <input
                type="text"
                value={newLabel}
                onChange={(e) => setNewLabel(e.target.value)}
                placeholder="Label (e.g. Daisy)"
                className="input w-full"
                autoFocus
              />
              {newLabel && (
                <p className="text-xs text-gray-500">
                  Value: <code className="bg-gray-200 px-1 rounded">{toSnakeCase(newLabel)}</code>
                </p>
              )}
              <input
                type="text"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Description (optional)"
                className="input w-full"
              />
              {isValueInvalid && (
                <p className="text-xs text-red-600">Label must contain at least one letter</p>
              )}
              {categoryType === 'glassware' && (
                <select
                  value={newGlasswareCategory}
                  onChange={(e) => setNewGlasswareCategory(e.target.value)}
                  className="select w-full"
                >
                  {GLASSWARE_GROUPS.map(g => (
                    <option key={g} value={g}>{g.charAt(0).toUpperCase() + g.slice(1)}</option>
                  ))}
                </select>
              )}
              {addError && <p className="text-sm text-red-600">{addError}</p>}
              <div className="flex gap-2">
                <button
                  onClick={handleAdd}
                  disabled={!newLabel.trim() || !generatedValue || createMutation.isPending}
                  className="btn btn-primary text-sm"
                >
                  {createMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    'Save'
                  )}
                </button>
                <button
                  onClick={() => { setShowAddForm(false); setAddError(''); setNewLabel(''); setNewDescription(''); }}
                  className="btn btn-secondary text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Category list */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : !categories || categories.length === 0 ? (
            <p className="text-gray-500 text-sm text-center py-4">No categories found</p>
          ) : (
            <>
              {/* Active categories */}
              <div className="space-y-1">
                {categories.filter(c => c.is_active).map((cat, index, activeList) => (
                  <div
                    key={cat.id}
                    className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 group"
                  >
                    {/* Reorder arrows */}
                    <div className="flex flex-col">
                      <button
                        onClick={() => handleReorder(categories.indexOf(cat), 'up')}
                        disabled={index === 0 || reorderMutation.isPending}
                        className="p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Move up"
                      >
                        <ChevronUp className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleReorder(categories.indexOf(cat), 'down')}
                        disabled={index === activeList.length - 1 || reorderMutation.isPending}
                        className="p-0.5 text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Move down"
                      >
                        <ChevronDown className="h-3.5 w-3.5" />
                      </button>
                    </div>

                    {/* Label (editable) */}
                    <div className="flex-1 min-w-0">
                      {editingId === cat.id ? (
                        <div className="flex items-center gap-1">
                          <input
                            ref={editInputRef}
                            type="text"
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onBlur={() => handleEditSave(cat.id)}
                            onKeyDown={(e) => handleEditKeyDown(e, cat.id)}
                            className="input text-sm py-0.5 flex-1"
                          />
                          {updateMutation.isPending && (
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-gray-400" />
                          )}
                        </div>
                      ) : (
                        <div>
                          <span
                            className="text-sm font-medium cursor-pointer hover:text-amber-600"
                            onClick={() => handleEditStart(cat)}
                          >
                            {cat.label}
                          </span>
                          <span className="text-xs text-gray-400 ml-2">{cat.value}</span>
                          {cat.category && (
                            <span className="text-xs text-gray-400 ml-1">({cat.category})</span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => handleEditStart(cat)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit label"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(cat)}
                        disabled={deleteMutation.isPending}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Deactivate"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Inactive categories — separate section */}
              {categories.some(c => !c.is_active) && (
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-500 uppercase mb-2">Disabled</p>
                  <div className="space-y-1">
                    {categories.filter(c => !c.is_active).map((cat) => (
                      <button
                        key={cat.id}
                        type="button"
                        onClick={() => handleReactivate(cat)}
                        disabled={updateMutation.isPending}
                        className="w-full flex items-center gap-2 p-3 rounded-lg bg-gray-50 border border-gray-200 text-left active:bg-green-50 active:border-green-300 disabled:opacity-50"
                      >
                        <RotateCcw className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <span className="text-sm text-gray-500 line-through">{cat.label}</span>
                          <span className="text-xs text-gray-400 ml-2">{cat.value}</span>
                        </div>
                        <span className="text-xs font-medium text-green-600">Tap to restore</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleClose}
            className="btn btn-secondary w-full"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
