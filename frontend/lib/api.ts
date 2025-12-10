/**
 * API client for cocktail backend.
 */

// Use environment variable for API URL, fallback to production URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://back-end-production-1219.up.railway.app/api';

// Backend base URL for static assets (uploads)
const BACKEND_BASE = API_BASE.replace(/\/api$/, '');

// Get full URL for uploaded images
export function getImageUrl(path?: string): string | undefined {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  // Ensure path starts with a slash
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${BACKEND_BASE}${normalizedPath}`;
}

export interface Ingredient {
  id: string;
  name: string;
  type: string;
  spirit_category?: string;
  description?: string;
}

export interface RecipeIngredient {
  id: string;
  amount?: number;
  unit?: string;
  notes?: string;
  optional: boolean;
  order: number;
  ingredient: Ingredient;
}

export interface Recipe {
  id: string;
  name: string;
  description?: string;
  instructions?: string;
  template?: string;
  main_spirit?: string;
  glassware?: string;
  serving_style?: string;
  method?: string;
  garnish?: string;
  notes?: string;
  source_image_path?: string;
  source_url?: string;
  source_type?: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  ingredients: RecipeIngredient[];
}

export interface RecipeListItem {
  id: string;
  name: string;
  template?: string;
  main_spirit?: string;
  glassware?: string;
  serving_style?: string;
  source_image_path?: string;
  user_id?: string;
  created_at: string;
}

export interface CategoryItem {
  value: string;
  display_name: string;
  description?: string;
}

export interface CategoryGroup {
  name: string;
  items: CategoryItem[];
}

export interface Categories {
  templates: CategoryItem[];
  spirits: CategoryItem[];
  glassware: CategoryGroup[];
  serving_styles: CategoryItem[];
  methods: CategoryItem[];
}

export interface RecipeFilters {
  template?: string;
  main_spirit?: string;
  glassware?: string;
  serving_style?: string;
  method?: string;
  search?: string;
}

export interface RecipeIngredientInput {
  ingredient_id?: string;
  ingredient_name?: string;
  ingredient_type?: string;
  amount?: number;
  unit?: string;
  notes?: string;
  optional?: boolean;
}

export interface RecipeInput {
  name: string;
  description?: string;
  instructions?: string;
  template?: string;
  main_spirit?: string;
  glassware?: string;
  serving_style?: string;
  method?: string;
  garnish?: string;
  notes?: string;
  ingredients?: RecipeIngredientInput[];
}

// Fetch all categories
export async function fetchCategories(): Promise<Categories> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

// Fetch recipes with filters
export async function fetchRecipes(filters: RecipeFilters = {}): Promise<RecipeListItem[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  const url = params.toString()
    ? `${API_BASE}/recipes?${params.toString()}`
    : `${API_BASE}/recipes`;

  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch recipes');
  return res.json();
}

// Fetch single recipe
export async function fetchRecipe(id: string): Promise<Recipe> {
  const res = await fetch(`${API_BASE}/recipes/${id}`);
  if (!res.ok) throw new Error('Recipe not found');
  return res.json();
}

// Upload and extract recipe
export async function uploadAndExtract(file: File, token?: string | null): Promise<Recipe> {
  const formData = new FormData();
  formData.append('file', file);

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/upload/extract-immediate`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Upload failed');
  }

  return res.json();
}

// Delete recipe
export async function deleteRecipe(id: string, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/recipes/${id}`, {
    method: 'DELETE',
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to delete recipe' }));
    throw new Error(error.detail || 'Failed to delete recipe');
  }
}

// Create recipe manually
export async function createRecipe(data: RecipeInput, token?: string | null): Promise<Recipe> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/recipes`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to create recipe' }));
    throw new Error(error.detail || 'Failed to create recipe');
  }

  return res.json();
}

// Update recipe
export async function updateRecipe(id: string, data: Partial<RecipeInput>, token?: string | null): Promise<Recipe> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/recipes/${id}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to update recipe' }));
    throw new Error(error.detail || 'Failed to update recipe');
  }

  return res.json();
}

// Format display helpers
export function formatEnumValue(value?: string): string {
  if (!value) return '';
  return value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function formatUnit(unit?: string, amount?: number): string {
  if (!unit) return '';

  const unitMap: Record<string, string> = {
    oz: 'oz',
    ml: 'ml',
    cl: 'cl',
    dash: amount === 1 ? 'dash' : 'dashes',
    drop: amount === 1 ? 'drop' : 'drops',
    barspoon: amount === 1 ? 'barspoon' : 'barspoons',
    tsp: 'tsp',
    tbsp: 'tbsp',
    rinse: 'rinse',
    float: 'float',
    top: 'top',
    whole: '',
    half: '',
    wedge: amount === 1 ? 'wedge' : 'wedges',
    slice: amount === 1 ? 'slice' : 'slices',
    peel: 'peel',
    sprig: amount === 1 ? 'sprig' : 'sprigs',
    leaf: amount === 1 ? 'leaf' : 'leaves',
  };

  return unitMap[unit] || unit;
}
