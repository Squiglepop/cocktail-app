import { http, HttpResponse } from 'msw'

// Use wildcard to match any host - this allows MSW to intercept both
// localhost and relative path requests
const API_BASE = '*/api'

// Mock data
export const mockUser = {
  id: '1',
  email: 'test@example.com',
  display_name: 'Test User',
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
    source_image_path: null,
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
    source_image_path: null,
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
  source_image_path: null,
  source_url: null,
  source_type: 'manual',
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
      source_image_path: null,
      source_url: null,
      source_type: 'manual',
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
]
