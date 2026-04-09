'use client';

import { useState, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import { AdminIngredient, AdminIngredientCreate, AdminIngredientUpdate, formatEnumValue } from '@/lib/api';

const INGREDIENT_TYPES = [
  'spirit', 'liqueur', 'wine_fortified', 'bitter', 'syrup',
  'juice', 'mixer', 'dairy', 'egg', 'garnish', 'other',
] as const;

const SPIRIT_CATEGORIES = [
  'gin', 'vodka', 'rum_light', 'rum_dark', 'rum_aged',
  'whiskey_bourbon', 'whiskey_rye', 'whiskey_scotch', 'whiskey_irish', 'whiskey_japanese',
  'tequila_blanco', 'tequila_reposado', 'tequila_anejo', 'mezcal',
  'brandy', 'cognac', 'pisco', 'aquavit', 'absinthe', 'cachaca',
  'baijiu', 'soju', 'sake', 'other',
] as const;

interface IngredientFormModalProps {
  isOpen: boolean;
  ingredient: AdminIngredient | null;
  onClose: () => void;
  onSave: (data: AdminIngredientCreate | AdminIngredientUpdate) => void;
  isSaving: boolean;
  error: string | null;
}

export function IngredientFormModal({
  isOpen,
  ingredient,
  onClose,
  onSave,
  isSaving,
  error,
}: IngredientFormModalProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState('spirit');
  const [spiritCategory, setSpiritCategory] = useState('');
  const [description, setDescription] = useState('');
  const [commonBrands, setCommonBrands] = useState('');

  const isEdit = ingredient !== null;

  useEffect(() => {
    if (isOpen) {
      if (ingredient) {
        setName(ingredient.name);
        setType(ingredient.type);
        setSpiritCategory(ingredient.spirit_category || '');
        setDescription(ingredient.description || '');
        setCommonBrands(ingredient.common_brands || '');
      } else {
        setName('');
        setType('spirit');
        setSpiritCategory('');
        setDescription('');
        setCommonBrands('');
      }
    }
  }, [isOpen, ingredient]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: AdminIngredientCreate = {
      name,
      type,
      ...(type === 'spirit' && spiritCategory ? { spirit_category: spiritCategory } : {}),
      ...(description ? { description } : {}),
      ...(commonBrands ? { common_brands: commonBrands } : {}),
    };
    onSave(data);
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-md w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? 'Edit Ingredient' : 'Add Ingredient'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="ingredient-name" className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              id="ingredient-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div>
            <label htmlFor="ingredient-type" className="block text-sm font-medium text-gray-700 mb-1">
              Type *
            </label>
            <select
              id="ingredient-type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
            >
              {INGREDIENT_TYPES.map((t) => (
                <option key={t} value={t}>{formatEnumValue(t)}</option>
              ))}
            </select>
          </div>

          {type === 'spirit' && (
            <div>
              <label htmlFor="spirit-category" className="block text-sm font-medium text-gray-700 mb-1">
                Spirit Category
              </label>
              <select
                id="spirit-category"
                value={spiritCategory}
                onChange={(e) => setSpiritCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                <option value="">Select category...</option>
                {SPIRIT_CATEGORIES.map((sc) => (
                  <option key={sc} value={sc}>{formatEnumValue(sc)}</option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label htmlFor="ingredient-description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="ingredient-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div>
            <label htmlFor="ingredient-brands" className="block text-sm font-medium text-gray-700 mb-1">
              Common Brands
            </label>
            <textarea
              id="ingredient-brands"
              value={commonBrands}
              onChange={(e) => setCommonBrands(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving || !name.trim()}
              className="btn bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50"
            >
              {isSaving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Saving...
                </>
              ) : (
                isEdit ? 'Update' : 'Create'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
