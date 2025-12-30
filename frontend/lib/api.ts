/**
 * API client for cocktail backend.
 */

// Use environment variable for API URL, fallback to localhost for development
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Get full URL for recipe images (served from database via API)
export function getRecipeImageUrl(recipeId: string): string {
  return `${API_BASE}/recipes/${recipeId}/image`;
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
  source_url?: string;
  source_type?: string;
  user_id?: string;
  visibility: string;
  my_rating?: number;
  has_image: boolean;
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
  has_image: boolean;
  user_id?: string;
  visibility: string;
  my_rating?: number;
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
  min_rating?: string;
  [key: string]: string | undefined;
}

export interface PaginationParams {
  skip?: number;
  limit?: number;
}

// Duplicate detection types
export interface DuplicateMatch {
  recipe_id: string;
  recipe_name: string;
  match_type: 'exact_image' | 'similar_image' | 'same_recipe';
  confidence: number;
  details: string;
}

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  matches: DuplicateMatch[];
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

// Fetch recipes with filters and pagination
export async function fetchRecipes(
  filters: RecipeFilters = {},
  pagination: PaginationParams = {},
  token?: string | null
): Promise<RecipeListItem[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  // Add pagination params
  if (pagination.skip !== undefined) {
    params.append('skip', pagination.skip.toString());
  }
  if (pagination.limit !== undefined) {
    params.append('limit', pagination.limit.toString());
  }

  const url = params.toString()
    ? `${API_BASE}/recipes?${params.toString()}`
    : `${API_BASE}/recipes`;

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('Failed to fetch recipes');
  return res.json();
}

export interface RecipeCount {
  total: number;
  filtered: number;
}

// Fetch recipe count (total and filtered)
export async function fetchRecipeCount(
  filters: RecipeFilters = {},
  token?: string | null
): Promise<RecipeCount> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });

  const url = params.toString()
    ? `${API_BASE}/recipes/count?${params.toString()}`
    : `${API_BASE}/recipes/count`;

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error('Failed to fetch recipe count');
  return res.json();
}

// Fetch single recipe
export async function fetchRecipe(id: string, token?: string | null): Promise<Recipe> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/recipes/${id}`, { headers });
  if (!res.ok) throw new Error('Recipe not found');
  return res.json();
}

// Check for duplicate images before extracting
export async function checkForDuplicates(file: File, token?: string | null): Promise<DuplicateCheckResult | null> {
  const formData = new FormData();
  formData.append('file', file);

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/upload?check_duplicates=true`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    return null; // Don't block on duplicate check failures
  }

  const data = await res.json();
  return data.duplicates || null;
}

// Upload and extract recipe (supports multiple files for multi-page recipes)
export async function uploadAndExtract(files: File | File[], token?: string | null): Promise<Recipe> {
  const formData = new FormData();
  const fileArray = Array.isArray(files) ? files : [files];

  if (fileArray.length === 1) {
    // Single file - use the original endpoint
    formData.append('file', fileArray[0]);

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
  } else {
    // Multiple files - use multi-file endpoint
    fileArray.forEach((file) => {
      formData.append('files', file);
    });

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}/upload/extract-multi`, {
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
}

// Enhance existing recipe with additional images
export async function enhanceRecipeWithImages(
  recipeId: string,
  files: File[],
  token?: string | null
): Promise<Recipe> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/upload/enhance/${recipeId}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Enhancement failed' }));
    throw new Error(error.detail || 'Enhancement failed');
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

// Update recipe rating (personal rating for any recipe)
export async function updateRecipeRating(id: string, rating: number | null, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (rating === null || rating === 0) {
    // Delete the rating
    const res = await fetch(`${API_BASE}/recipes/${id}/my-rating`, {
      method: 'DELETE',
      headers,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to clear rating' }));
      throw new Error(error.detail || 'Failed to clear rating');
    }
  } else {
    // Set/update the rating
    const res = await fetch(`${API_BASE}/recipes/${id}/my-rating`, {
      method: 'PUT',
      headers,
      body: JSON.stringify({ rating }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Failed to update rating' }));
      throw new Error(error.detail || 'Failed to update rating');
    }
  }
}

// Rating captions (cricket-themed)
export const RATING_CAPTIONS: Record<number, string> = {
  5: 'KW',
  4: 'J Root',
  3: 'V-Rat',
  2: 'Monty Panesar',
  1: '"We saw you cry on the telly"',
};

// Collection (Playlist) types
export interface Collection {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  user_id: string;
  recipe_count: number;
  created_at: string;
  updated_at: string;
}

export interface CollectionListItem {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  recipe_count: number;
  created_at: string;
  is_shared?: boolean;
  can_edit?: boolean;
  owner_name?: string;
}

export interface CollectionRecipe {
  id: string;
  recipe_id: string;
  recipe_name: string;
  recipe_template?: string;
  recipe_main_spirit?: string;
  recipe_has_image: boolean;
  position: number;
  added_at: string;
}

export interface CollectionDetail extends Collection {
  recipes: CollectionRecipe[];
  is_shared?: boolean;
  can_edit?: boolean;
}

export interface CollectionInput {
  name: string;
  description?: string;
  is_public?: boolean;
}

// Fetch user's collections
export async function fetchCollections(token?: string | null): Promise<CollectionListItem[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections`, { headers });
  if (!res.ok) throw new Error('Failed to fetch collections');
  return res.json();
}

// Fetch single collection with recipes
export async function fetchCollection(id: string, token?: string | null): Promise<CollectionDetail> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${id}`, { headers });
  if (!res.ok) throw new Error('Collection not found');
  return res.json();
}

// Create collection
export async function createCollection(data: CollectionInput, token?: string | null): Promise<Collection> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections`, {
    method: 'POST',
    headers,
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to create collection' }));
    throw new Error(error.detail || 'Failed to create collection');
  }

  return res.json();
}

// Update collection
export async function updateCollection(id: string, data: Partial<CollectionInput>, token?: string | null): Promise<Collection> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${id}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to update collection' }));
    throw new Error(error.detail || 'Failed to update collection');
  }

  return res.json();
}

// Delete collection
export async function deleteCollection(id: string, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${id}`, {
    method: 'DELETE',
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to delete collection' }));
    throw new Error(error.detail || 'Failed to delete collection');
  }
}

// Add recipe to collection
export async function addRecipeToCollection(collectionId: string, recipeId: string, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/recipes`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ recipe_id: recipeId }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to add recipe to collection' }));
    throw new Error(error.detail || 'Failed to add recipe to collection');
  }
}

// Remove recipe from collection
export async function removeRecipeFromCollection(collectionId: string, recipeId: string, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/recipes/${recipeId}`, {
    method: 'DELETE',
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to remove recipe from collection' }));
    throw new Error(error.detail || 'Failed to remove recipe from collection');
  }
}

// Reorder recipes in collection
export async function reorderCollectionRecipes(collectionId: string, reorderData: { recipe_id: string; position: number }[], token?: string | null): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/recipes/reorder`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(reorderData),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to reorder recipes' }));
    throw new Error(error.detail || 'Failed to reorder recipes');
  }
}

// Collection sharing types
export interface CollectionShare {
  id: string;
  collection_id: string;
  shared_with_user_id: string;
  shared_with_email: string;
  shared_with_display_name?: string;
  can_edit: boolean;
  shared_at: string;
}

// Fetch collection shares
export async function fetchCollectionShares(collectionId: string, token?: string | null): Promise<CollectionShare[]> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/shares`, { headers });
  if (!res.ok) throw new Error('Failed to fetch shares');
  const data = await res.json();
  return data.shares;
}

// Share collection with user by email
export async function shareCollection(collectionId: string, email: string, canEdit: boolean = false, token?: string | null): Promise<CollectionShare> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/shares`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ email, can_edit: canEdit }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to share collection' }));
    throw new Error(error.detail || 'Failed to share collection');
  }

  return res.json();
}

// Update collection share permissions
export async function updateCollectionShare(collectionId: string, shareId: string, canEdit: boolean, token?: string | null): Promise<CollectionShare> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/shares/${shareId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ can_edit: canEdit }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to update share' }));
    throw new Error(error.detail || 'Failed to update share');
  }

  return res.json();
}

// Remove collection share
export async function removeCollectionShare(collectionId: string, shareId: string, token?: string | null): Promise<void> {
  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/collections/${collectionId}/shares/${shareId}`, {
    method: 'DELETE',
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Failed to remove share' }));
    throw new Error(error.detail || 'Failed to remove share');
  }
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
    grams: amount === 1 ? 'gram' : 'grams',
  };

  return unitMap[unit] || unit;
}
