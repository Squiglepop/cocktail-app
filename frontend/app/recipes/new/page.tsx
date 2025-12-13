'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Categories,
  RecipeInput,
  fetchCategories,
  createRecipe,
  formatEnumValue,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { ArrowLeft, Plus, Trash2, Save, Loader2 } from 'lucide-react';

interface IngredientFormData {
  ingredient_name: string;
  ingredient_type: string;
  amount: string;
  unit: string;
  notes: string;
  optional: boolean;
}

export default function NewRecipePage() {
  const router = useRouter();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Categories | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');
  const [template, setTemplate] = useState('');
  const [mainSpirit, setMainSpirit] = useState('');
  const [glassware, setGlassware] = useState('');
  const [servingStyle, setServingStyle] = useState('');
  const [method, setMethod] = useState('');
  const [garnish, setGarnish] = useState('');
  const [notes, setNotes] = useState('');
  const [ingredients, setIngredients] = useState<IngredientFormData[]>([
    {
      ingredient_name: '',
      ingredient_type: 'spirit',
      amount: '',
      unit: 'oz',
      notes: '',
      optional: false,
    },
  ]);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch((err) => {
        setError('Failed to load categories');
        console.error(err);
      })
      .finally(() => setLoading(false));
  }, []);

  const addIngredient = () => {
    setIngredients([
      ...ingredients,
      {
        ingredient_name: '',
        ingredient_type: 'other',
        amount: '',
        unit: 'oz',
        notes: '',
        optional: false,
      },
    ]);
  };

  const removeIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const updateIngredient = (index: number, field: keyof IngredientFormData, value: string | boolean) => {
    setIngredients(
      ingredients.map((ing, i) =>
        i === index ? { ...ing, [field]: value } : ing
      )
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const recipeData: RecipeInput = {
        name,
        description: description || undefined,
        instructions: instructions || undefined,
        template: template || undefined,
        main_spirit: mainSpirit || undefined,
        glassware: glassware || undefined,
        serving_style: servingStyle || undefined,
        method: method || undefined,
        garnish: garnish || undefined,
        notes: notes || undefined,
        ingredients: ingredients
          .filter((ing) => ing.ingredient_name.trim())
          .map((ing) => ({
            ingredient_name: ing.ingredient_name,
            ingredient_type: ing.ingredient_type,
            amount: ing.amount ? parseFloat(ing.amount) : undefined,
            unit: ing.unit || undefined,
            notes: ing.notes || undefined,
            optional: ing.optional,
          })),
      };

      const recipe = await createRecipe(recipeData, token);
      router.push(`/recipes/${recipe.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create recipe');
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
        </div>
      </div>
    );
  }

  if (!categories) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error || 'Failed to load'}</p>
          <Link href="/" className="text-amber-600 hover:text-amber-700">
            Back to recipes
          </Link>
        </div>
      </div>
    );
  }

  const units = ['oz', 'ml', 'cl', 'dash', 'drop', 'barspoon', 'tsp', 'tbsp', 'rinse', 'float', 'top', 'whole', 'half', 'wedge', 'slice', 'peel', 'sprig', 'leaf'];
  const ingredientTypes = ['spirit', 'liqueur', 'wine_fortified', 'bitter', 'syrup', 'juice', 'mixer', 'dairy', 'egg', 'garnish', 'other'];

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to recipes
      </Link>

      <h1 className="text-3xl font-bold text-gray-900 mb-8">Add New Recipe</h1>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Info */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Basic Info</h2>

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name *
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="input w-full"
              placeholder="e.g., Whiskey Sour"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="input w-full"
              placeholder="A brief description of the cocktail..."
            />
          </div>
        </section>

        {/* Classification */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Classification</h2>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="template" className="block text-sm font-medium text-gray-700 mb-1">
                Template
              </label>
              <select
                id="template"
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
                className="input w-full"
              >
                <option value="">Select template...</option>
                {categories.templates.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.display_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="mainSpirit" className="block text-sm font-medium text-gray-700 mb-1">
                Main Spirit
              </label>
              <select
                id="mainSpirit"
                value={mainSpirit}
                onChange={(e) => setMainSpirit(e.target.value)}
                className="input w-full"
              >
                <option value="">Select spirit...</option>
                {categories.spirits.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.display_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="method" className="block text-sm font-medium text-gray-700 mb-1">
                Method
              </label>
              <select
                id="method"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="input w-full"
              >
                <option value="">Select method...</option>
                {categories.methods.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.display_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="glassware" className="block text-sm font-medium text-gray-700 mb-1">
                Glassware
              </label>
              <select
                id="glassware"
                value={glassware}
                onChange={(e) => setGlassware(e.target.value)}
                className="input w-full"
              >
                <option value="">Select glassware...</option>
                {categories.glassware.map((group) => (
                  <optgroup key={group.name} label={group.name}>
                    {group.items.map((g) => (
                      <option key={g.value} value={g.value}>
                        {g.display_name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="servingStyle" className="block text-sm font-medium text-gray-700 mb-1">
                Serving Style
              </label>
              <select
                id="servingStyle"
                value={servingStyle}
                onChange={(e) => setServingStyle(e.target.value)}
                className="input w-full"
              >
                <option value="">Select style...</option>
                {categories.serving_styles.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.display_name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {/* Ingredients */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Ingredients</h2>
            <button
              type="button"
              onClick={addIngredient}
              className="btn btn-secondary text-sm"
            >
              <Plus className="h-4 w-4 mr-1" />
              Add Ingredient
            </button>
          </div>

          <div className="space-y-3">
            {ingredients.map((ing, index) => (
              <div key={index} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 grid grid-cols-2 md:grid-cols-6 gap-2">
                  <input
                    type="text"
                    value={ing.amount}
                    onChange={(e) => updateIngredient(index, 'amount', e.target.value)}
                    placeholder="Amount"
                    className="input"
                  />
                  <select
                    value={ing.unit}
                    onChange={(e) => updateIngredient(index, 'unit', e.target.value)}
                    className="input"
                  >
                    {units.map((u) => (
                      <option key={u} value={u}>
                        {u}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={ing.ingredient_name}
                    onChange={(e) => updateIngredient(index, 'ingredient_name', e.target.value)}
                    placeholder="Ingredient name"
                    className="input md:col-span-2"
                  />
                  <select
                    value={ing.ingredient_type}
                    onChange={(e) => updateIngredient(index, 'ingredient_type', e.target.value)}
                    className="input"
                  >
                    {ingredientTypes.map((t) => (
                      <option key={t} value={t}>
                        {formatEnumValue(t)}
                      </option>
                    ))}
                  </select>
                  <label className="flex items-center gap-1 text-sm text-gray-600">
                    <input
                      type="checkbox"
                      checked={ing.optional}
                      onChange={(e) => updateIngredient(index, 'optional', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    Optional
                  </label>
                </div>
                <button
                  type="button"
                  onClick={() => removeIngredient(index)}
                  className="p-2 text-gray-400 hover:text-red-600"
                  disabled={ingredients.length === 1}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Garnish & Instructions */}
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Preparation</h2>

          <div>
            <label htmlFor="garnish" className="block text-sm font-medium text-gray-700 mb-1">
              Garnish
            </label>
            <input
              type="text"
              id="garnish"
              value={garnish}
              onChange={(e) => setGarnish(e.target.value)}
              className="input w-full"
              placeholder="e.g., Lemon twist, cherry"
            />
          </div>

          <div>
            <label htmlFor="instructions" className="block text-sm font-medium text-gray-700 mb-1">
              Instructions
            </label>
            <textarea
              id="instructions"
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={4}
              className="input w-full"
              placeholder="Step-by-step preparation instructions..."
            />
          </div>

          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="input w-full"
              placeholder="Additional notes, tips, or variations..."
            />
          </div>
        </section>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4 pt-6 border-t border-gray-200">
          <Link
            href="/"
            className="btn btn-ghost"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving || !name.trim()}
            className="btn btn-primary"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Create Recipe
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
