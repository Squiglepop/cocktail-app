import { http, HttpResponse } from 'msw'

// Use wildcard to match any host - this allows MSW to intercept both
// localhost and relative path requests
const API_BASE = '*/api'

// Mock data
export const mockUser = {
  id: '1',
  email: 'test@example.com',
  display_name: 'Test User',
  is_admin: false,
  created_at: '2024-01-01T00:00:00Z',
}

export const mockRecipes = [
  {
    id: '1',
    name: 'Margarita',
    template: 'sour',
    main_spirit: 'tequila',
    glassware: 'coupe',
    serving_style: 'up',
    has_image: false,
    user_id: '1',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    name: 'Old Fashioned',
    template: 'old_fashioned',
    main_spirit: 'bourbon',
    glassware: 'rocks',
    serving_style: 'rocks',
    has_image: false,
    user_id: null,
    created_at: '2024-01-02T00:00:00Z',
  },
]

export const mockRecipeDetail = {
  id: '1',
  name: 'Margarita',
  description: 'A classic tequila cocktail',
  instructions: 'Shake all ingredients with ice. Strain into a salt-rimmed glass.',
  template: 'sour',
  main_spirit: 'tequila',
  glassware: 'coupe',
  serving_style: 'up',
  method: 'shaken',
  garnish: 'Lime wheel',
  notes: 'Classic recipe',
  source_url: null,
  source_type: 'manual',
  has_image: false,
  user_id: '1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ingredients: [
    {
      id: '1',
      amount: 2,
      unit: 'oz',
      notes: null,
      optional: false,
      order: 0,
      ingredient: {
        id: '1',
        name: 'Tequila',
        type: 'spirit',
        spirit_category: 'tequila',
        description: null,
        common_brands: null,
      },
    },
    {
      id: '2',
      amount: 1,
      unit: 'oz',
      notes: 'fresh',
      optional: false,
      order: 1,
      ingredient: {
        id: '2',
        name: 'Lime Juice',
        type: 'juice',
        spirit_category: null,
        description: null,
        common_brands: null,
      },
    },
  ],
}

export const mockAdminUsers = [
  {
    id: '1', email: 'admin@test.com', display_name: 'Admin User',
    is_active: true, is_admin: true, recipe_count: 10,
    created_at: '2026-01-01T00:00:00Z', last_login_at: '2026-04-08T12:00:00Z',
  },
  {
    id: '2', email: 'user@test.com', display_name: 'Regular User',
    is_active: true, is_admin: false, recipe_count: 5,
    created_at: '2026-02-01T00:00:00Z', last_login_at: '2026-04-07T12:00:00Z',
  },
  {
    id: '3', email: 'inactive@test.com', display_name: null,
    is_active: false, is_admin: false, recipe_count: 0,
    created_at: '2026-03-01T00:00:00Z', last_login_at: null,
  },
  {
    id: '4', email: 'otheradmin@test.com', display_name: 'Other Admin',
    is_active: true, is_admin: true, recipe_count: 8,
    created_at: '2026-01-15T00:00:00Z', last_login_at: '2026-04-09T10:00:00Z',
  },
]

export const mockAdminIngredients = [
  { id: '1', name: 'Lime Juice', type: 'juice', spirit_category: null, description: 'Fresh lime juice', common_brands: null },
  { id: '2', name: 'Simple Syrup', type: 'syrup', spirit_category: null, description: '1:1 sugar water', common_brands: null },
  { id: '3', name: 'London Dry Gin', type: 'spirit', spirit_category: 'gin', description: 'Classic gin style', common_brands: 'Beefeater, Tanqueray' },
]

export const mockDuplicateIngredientResponse = {
  groups: [
    {
      target: { ingredient_id: '1', name: 'Lime Juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 15 },
      duplicates: [
        { ingredient_id: '10', name: 'lime juice', type: 'juice', similarity_score: 1.0, detection_reason: 'exact_match_case_insensitive', usage_count: 3 },
      ],
      group_reason: 'exact_match_case_insensitive',
    },
  ],
  total_groups: 1,
  total_duplicates: 1,
}

export const mockAuditLogs = [
  {
    id: 'audit-1', admin_user_id: '1', admin_email: 'admin@test.com',
    action: 'category_create', entity_type: 'category', entity_id: 'cat-1',
    details: { type: 'templates', value: 'tiki', label: 'Tiki' },
    created_at: '2026-04-09T14:00:00Z',
  },
  {
    id: 'audit-2', admin_user_id: '1', admin_email: 'admin@test.com',
    action: 'recipe_admin_delete', entity_type: 'recipe', entity_id: 'rec-1',
    details: { recipe_name: 'Old Fashioned', owner_id: '2' },
    created_at: '2026-04-09T13:00:00Z',
  },
  {
    id: 'audit-3', admin_user_id: '1', admin_email: 'admin@test.com',
    action: 'user_deactivate', entity_type: 'user', entity_id: 'user-3',
    details: { email: 'banned@test.com' },
    created_at: '2026-04-08T10:00:00Z',
  },
  {
    id: 'audit-4', admin_user_id: '1', admin_email: null,
    action: 'ingredient_merge', entity_type: 'ingredient', entity_id: null,
    details: { source_ids: ['ing-1', 'ing-2'], target_id: 'ing-3', recipes_updated: 5 },
    created_at: '2026-04-07T09:00:00Z',
  },
  {
    id: 'audit-5', admin_user_id: '1', admin_email: 'admin@test.com',
    action: 'category_delete', entity_type: 'category', entity_id: 'cat-99',
    details: null,
    created_at: '2026-04-06T08:00:00Z',
  },
]

export const mockAdminCategories = [
  { id: '1', value: 'sour', label: 'Sour', description: 'Spirit, citrus, sweetener', category: null, sort_order: 0, is_active: true, created_at: '2026-01-01T00:00:00Z' },
  { id: '2', value: 'old_fashioned', label: 'Old Fashioned', description: 'Spirit, sugar, bitters', category: null, sort_order: 1, is_active: true, created_at: '2026-01-01T00:00:00Z' },
  { id: '3', value: 'flip', label: 'Flip', description: 'Egg-based', category: null, sort_order: 2, is_active: false, created_at: '2026-01-01T00:00:00Z' },
]

export const mockCategories = {
  templates: [
    { value: 'sour', display_name: 'Sour', description: 'Spirit, citrus, and sweetener' },
    { value: 'old_fashioned', display_name: 'Old Fashioned', description: 'Spirit, sugar, bitters' },
    { value: 'martini', display_name: 'Martini', description: 'Spirit and vermouth' },
    { value: 'negroni', display_name: 'Negroni', description: 'Equal parts spirit, bitter, vermouth' },
  ],
  spirits: [
    { value: 'vodka', display_name: 'Vodka' },
    { value: 'gin', display_name: 'Gin' },
    { value: 'tequila', display_name: 'Tequila' },
    { value: 'bourbon', display_name: 'Bourbon' },
    { value: 'rum', display_name: 'Rum' },
  ],
  glassware: [
    {
      name: 'Stemmed',
      items: [
        { value: 'coupe', display_name: 'Coupe' },
        { value: 'martini', display_name: 'Martini Glass' },
      ],
    },
    {
      name: 'Short',
      items: [
        { value: 'rocks', display_name: 'Rocks Glass' },
        { value: 'double_rocks', display_name: 'Double Rocks' },
      ],
    },
    {
      name: 'Tall',
      items: [
        { value: 'highball', display_name: 'Highball' },
        { value: 'collins', display_name: 'Collins' },
      ],
    },
  ],
  serving_styles: [
    { value: 'up', display_name: 'Up', description: 'Chilled, no ice' },
    { value: 'rocks', display_name: 'Rocks', description: 'Over ice' },
    { value: 'neat', display_name: 'Neat', description: 'Room temperature, no ice' },
  ],
  methods: [
    { value: 'shaken', display_name: 'Shaken', description: 'Shaken with ice' },
    { value: 'stirred', display_name: 'Stirred', description: 'Stirred with ice' },
    { value: 'built', display_name: 'Built', description: 'Built in glass' },
  ],
}

// Request handlers
export const handlers = [
  // Auth endpoints
  http.post(`${API_BASE}/auth/register`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string; display_name?: string }

    if (body.email === 'existing@example.com') {
      return HttpResponse.json(
        { detail: 'Email already registered' },
        { status: 400 }
      )
    }

    return HttpResponse.json(
      {
        id: '2',
        email: body.email,
        display_name: body.display_name || null,
        created_at: new Date().toISOString(),
      },
      { status: 201 }
    )
  }),

  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }

    if (body.email === 'test@example.com' && body.password === 'testpassword123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
      })
    }

    return HttpResponse.json(
      { detail: 'Incorrect email or password' },
      { status: 401 }
    )
  }),

  http.get(`${API_BASE}/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')

    if (authHeader === 'Bearer mock-jwt-token') {
      return HttpResponse.json(mockUser)
    }

    return HttpResponse.json(
      { detail: 'Not authenticated' },
      { status: 401 }
    )
  }),

  http.put(`${API_BASE}/auth/me`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization')

    if (authHeader !== 'Bearer mock-jwt-token') {
      return HttpResponse.json(
        { detail: 'Not authenticated' },
        { status: 401 }
      )
    }

    const body = (await request.json()) as { display_name?: string }
    return HttpResponse.json({
      ...mockUser,
      display_name: body.display_name || mockUser.display_name,
    })
  }),

  http.post(`${API_BASE}/auth/refresh`, () => {
    // Return new access token (simulates cookie-based refresh)
    return HttpResponse.json({
      access_token: 'mock-jwt-token-refreshed',
      token_type: 'bearer',
    })
  }),

  http.post(`${API_BASE}/auth/logout`, () => {
    return HttpResponse.json({ message: 'Successfully logged out' })
  }),

  // Recipe endpoints
  http.get(`${API_BASE}/recipes`, ({ request }) => {
    const url = new URL(request.url)
    const template = url.searchParams.get('template')
    const main_spirit = url.searchParams.get('main_spirit')
    const search = url.searchParams.get('search')

    let filtered = [...mockRecipes]

    if (template) {
      filtered = filtered.filter((r) => r.template === template)
    }
    if (main_spirit) {
      filtered = filtered.filter((r) => r.main_spirit === main_spirit)
    }
    if (search) {
      filtered = filtered.filter((r) =>
        r.name.toLowerCase().includes(search.toLowerCase())
      )
    }

    return HttpResponse.json(filtered)
  }),

  http.get(`${API_BASE}/recipes/count`, ({ request }) => {
    const url = new URL(request.url)
    const template = url.searchParams.get('template')
    const main_spirit = url.searchParams.get('main_spirit')
    const search = url.searchParams.get('search')

    let filtered = [...mockRecipes]

    if (template) {
      filtered = filtered.filter((r) => r.template === template)
    }
    if (main_spirit) {
      filtered = filtered.filter((r) => r.main_spirit === main_spirit)
    }
    if (search) {
      filtered = filtered.filter((r) =>
        r.name.toLowerCase().includes(search.toLowerCase())
      )
    }

    return HttpResponse.json({
      total: mockRecipes.length,
      filtered: filtered.length,
    })
  }),

  http.get(`${API_BASE}/recipes/:id`, ({ params }) => {
    const { id } = params

    if (id === '1') {
      return HttpResponse.json(mockRecipeDetail)
    }

    return HttpResponse.json(
      { detail: 'Recipe not found' },
      { status: 404 }
    )
  }),

  http.post(`${API_BASE}/recipes`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    const body = (await request.json()) as { name: string; [key: string]: unknown }

    return HttpResponse.json({
      id: '3',
      name: body.name,
      description: body.description || null,
      instructions: body.instructions || null,
      template: body.template || null,
      main_spirit: body.main_spirit || null,
      glassware: body.glassware || null,
      serving_style: body.serving_style || null,
      method: body.method || null,
      garnish: body.garnish || null,
      notes: body.notes || null,
      source_url: null,
      source_type: 'manual',
      has_image: false,
      user_id: authHeader ? '1' : null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ingredients: [],
    })
  }),

  http.put(`${API_BASE}/recipes/:id`, async ({ params, request }) => {
    const { id } = params
    const authHeader = request.headers.get('Authorization')
    const body = (await request.json()) as Record<string, unknown>

    if (id !== '1' && id !== '2') {
      return HttpResponse.json(
        { detail: 'Recipe not found' },
        { status: 404 }
      )
    }

    // Recipe 1 requires auth
    if (id === '1' && authHeader !== 'Bearer mock-jwt-token') {
      return HttpResponse.json(
        { detail: 'Authentication required to edit this recipe' },
        { status: 401 }
      )
    }

    return HttpResponse.json({
      ...mockRecipeDetail,
      ...body,
      updated_at: new Date().toISOString(),
    })
  }),

  http.delete(`${API_BASE}/recipes/:id`, ({ params, request }) => {
    const { id } = params
    const authHeader = request.headers.get('Authorization')

    if (id !== '1' && id !== '2') {
      return HttpResponse.json(
        { detail: 'Recipe not found' },
        { status: 404 }
      )
    }

    // Recipe 1 requires auth
    if (id === '1' && authHeader !== 'Bearer mock-jwt-token') {
      return HttpResponse.json(
        { detail: 'Authentication required to delete this recipe' },
        { status: 401 }
      )
    }

    return HttpResponse.json({ message: 'Recipe deleted successfully' })
  }),

  // Category endpoints
  http.get(`${API_BASE}/categories`, () => {
    return HttpResponse.json(mockCategories)
  }),

  http.get(`${API_BASE}/categories/templates`, () => {
    return HttpResponse.json(mockCategories.templates)
  }),

  http.get(`${API_BASE}/categories/spirits`, () => {
    return HttpResponse.json(mockCategories.spirits)
  }),

  http.get(`${API_BASE}/categories/glassware`, () => {
    return HttpResponse.json(
      mockCategories.glassware.map((g) => ({
        category: g.name.toLowerCase(),
        name: g.name,
        items: g.items,
      }))
    )
  }),

  http.get(`${API_BASE}/categories/serving-styles`, () => {
    return HttpResponse.json(mockCategories.serving_styles)
  }),

  http.get(`${API_BASE}/categories/methods`, () => {
    return HttpResponse.json(mockCategories.methods)
  }),

  // Upload endpoints
  http.post(`${API_BASE}/upload`, async () => {
    return HttpResponse.json({
      id: 'job-1',
      status: 'pending',
      image_path: '/uploads/test.png',
      recipe_id: null,
      error_message: null,
      created_at: new Date().toISOString(),
      completed_at: null,
    })
  }),

  http.post(`${API_BASE}/upload/:jobId/extract`, ({ params }) => {
    const { jobId } = params

    if (jobId === 'job-1') {
      return HttpResponse.json({
        id: '4',
        name: 'Extracted Cocktail',
        description: 'Extracted from image',
        template: 'sour',
        main_spirit: 'vodka',
        ingredients: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    }

    return HttpResponse.json(
      { detail: 'Job not found' },
      { status: 404 }
    )
  }),

  http.post(`${API_BASE}/upload/extract-immediate`, async () => {
    return HttpResponse.json({
      id: '5',
      name: 'Immediate Extraction',
      description: 'Extracted immediately',
      template: 'highball',
      main_spirit: 'gin',
      ingredients: [],
      source_type: 'screenshot',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    })
  }),

  http.get(`${API_BASE}/upload/:jobId`, ({ params }) => {
    const { jobId } = params

    if (jobId === 'job-1') {
      return HttpResponse.json({
        id: 'job-1',
        status: 'completed',
        image_path: '/uploads/test.png',
        recipe_id: '4',
        error_message: null,
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      })
    }

    return HttpResponse.json(
      { detail: 'Job not found' },
      { status: 404 }
    )
  }),

  // Admin category endpoints
  http.get(`${API_BASE}/admin/categories/:type`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    return HttpResponse.json(mockAdminCategories)
  }),

  http.post(`${API_BASE}/admin/categories/:type/reorder`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    return HttpResponse.json({ message: 'Categories reordered successfully' })
  }),

  http.post(`${API_BASE}/admin/categories/:type`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { value: string; label: string; description?: string }
    if (body.value === 'sour') return HttpResponse.json({ detail: 'Category value already exists' }, { status: 409 })
    return HttpResponse.json({ id: '99', ...body, category: null, sort_order: 99, is_active: true, created_at: new Date().toISOString() }, { status: 201 })
  }),

  http.put(`${API_BASE}/admin/categories/:type/:id`, async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as Record<string, unknown>
    const existing = mockAdminCategories.find(c => c.id === params.id)
    if (!existing) return HttpResponse.json({ detail: 'Category not found' }, { status: 404 })
    return HttpResponse.json({ ...existing, ...body })
  }),

  http.delete(`${API_BASE}/admin/categories/:type/:id`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    return HttpResponse.json({ message: 'Category deactivated', recipe_count: 3 })
  }),

  // Admin ingredient endpoints
  http.get(`${API_BASE}/admin/ingredients/duplicates`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    return HttpResponse.json(mockDuplicateIngredientResponse)
  }),

  http.get(`${API_BASE}/admin/ingredients`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const url = new URL(request.url)
    const search = url.searchParams.get('search')
    const type = url.searchParams.get('type')
    let items = [...mockAdminIngredients]
    if (search) items = items.filter(i => i.name.toLowerCase().includes(search.toLowerCase()))
    if (type) items = items.filter(i => i.type === type)
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 50 })
  }),

  http.post(`${API_BASE}/admin/ingredients`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as { name: string; type: string }
    if (body.name.toLowerCase() === 'lime juice') {
      return HttpResponse.json({ detail: 'Ingredient with this name already exists' }, { status: 409 })
    }
    return HttpResponse.json({ id: '99', ...body, spirit_category: null, description: null, common_brands: null }, { status: 201 })
  }),

  http.put(`${API_BASE}/admin/ingredients/:id`, async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as Record<string, unknown>
    const existing = mockAdminIngredients.find(i => i.id === params.id)
    if (!existing) return HttpResponse.json({ detail: 'Ingredient not found' }, { status: 404 })
    return HttpResponse.json({ ...existing, ...body })
  }),

  http.delete(`${API_BASE}/admin/ingredients/:id`, ({ params, request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    if (params.id === '1') {
      return HttpResponse.json({ message: 'Cannot delete ingredient used in recipes', recipe_count: 15 }, { status: 409 })
    }
    return new HttpResponse(null, { status: 200 })
  }),

  http.post(`${API_BASE}/admin/ingredients/merge`, async ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    return HttpResponse.json({ message: 'Ingredients merged', recipes_affected: 3, sources_removed: 1 })
  }),

  // Admin user endpoints
  http.get(`${API_BASE}/admin/users`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const url = new URL(request.url)
    const search = url.searchParams.get('search')
    const status = url.searchParams.get('status')
    let items = [...mockAdminUsers]
    if (search) {
      items = items.filter(u =>
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        (u.display_name && u.display_name.toLowerCase().includes(search.toLowerCase()))
      )
    }
    if (status === 'active') items = items.filter(u => u.is_active)
    if (status === 'inactive') items = items.filter(u => !u.is_active)
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 50 })
  }),

  http.patch(`${API_BASE}/admin/users/:id`, async ({ params, request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const body = await request.json() as Record<string, unknown>
    const user = mockAdminUsers.find(u => u.id === params.id)
    if (!user) return HttpResponse.json({ detail: 'User not found' }, { status: 404 })
    if (params.id === '1') {
      if (body.is_active === false) {
        return HttpResponse.json({ detail: 'Cannot deactivate your own account' }, { status: 400 })
      }
      if (body.is_admin === false) {
        return HttpResponse.json({ detail: 'Cannot remove your own admin status' }, { status: 400 })
      }
    }
    const updated = { ...user, ...body }
    const parts: string[] = []
    if (body.is_active !== undefined) {
      parts.push(body.is_active ? 'User activated' : 'User deactivated')
    }
    if (body.is_admin !== undefined) {
      parts.push(body.is_admin ? 'User granted admin' : 'User revoked admin')
    }
    if (body.display_name !== undefined) {
      parts.push(`display_name updated to '${body.display_name}'`)
    }
    const message = parts.length > 0 ? parts.join(', ') : 'No changes applied'
    return HttpResponse.json({
      id: updated.id, email: updated.email, display_name: updated.display_name,
      is_active: updated.is_active, is_admin: updated.is_admin,
      message,
    })
  }),

  // Admin audit log endpoint
  http.get(`${API_BASE}/admin/audit-log`, ({ request }) => {
    const authHeader = request.headers.get('Authorization')
    if (!authHeader) return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    const url = new URL(request.url)
    const action = url.searchParams.get('action')
    const entityType = url.searchParams.get('entity_type')
    const from = url.searchParams.get('from')
    const to = url.searchParams.get('to')
    let items = [...mockAuditLogs]
    if (action) items = items.filter(e => e.action === action)
    if (entityType) items = items.filter(e => e.entity_type === entityType)
    if (from) items = items.filter(e => e.created_at >= new Date(from).toISOString())
    if (to) {
      const toEnd = new Date(to)
      toEnd.setDate(toEnd.getDate() + 1)
      items = items.filter(e => e.created_at < toEnd.toISOString())
    }
    return HttpResponse.json({ items, total: items.length, page: 1, per_page: 20 })
  }),

  // Health check endpoint (for offline detection)
  // The OfflineProvider constructs URL as: API_BASE.replace(/\/api\/?$/, '') + '/health'
  // Which becomes something like http://localhost:8000/health
  http.get(/.*\/health.*/, () => {
    return HttpResponse.json({ status: 'healthy' })
  }),
]
