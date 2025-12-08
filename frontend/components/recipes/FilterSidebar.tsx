'use client';

import { useEffect, useState } from 'react';
import { Categories, CategoryItem, CategoryGroup, fetchCategories } from '@/lib/api';
import { X } from 'lucide-react';

interface FilterSidebarProps {
  filters: {
    template?: string;
    main_spirit?: string;
    glassware?: string;
    serving_style?: string;
    search?: string;
  };
  onFilterChange: (filters: FilterSidebarProps['filters']) => void;
}

export function FilterSidebar({ filters, onFilterChange }: FilterSidebarProps) {
  const [categories, setCategories] = useState<Categories | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const updateFilter = (key: string, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value || undefined,
    });
  };

  const clearFilters = () => {
    onFilterChange({});
  };

  const hasActiveFilters = Object.values(filters).some(v => v);

  if (loading) {
    return (
      <div className="w-64 shrink-0">
        <div className="card p-4">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!categories) return null;

  return (
    <div className="w-64 shrink-0">
      <div className="card p-4 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">Filters</h2>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-xs text-amber-600 hover:text-amber-700 flex items-center gap-1"
            >
              <X className="h-3 w-3" />
              Clear all
            </button>
          )}
        </div>

        {/* Search */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search
          </label>
          <input
            type="text"
            placeholder="Search recipes..."
            value={filters.search || ''}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="input"
          />
        </div>

        {/* Template */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Template / Family
          </label>
          <select
            value={filters.template || ''}
            onChange={(e) => updateFilter('template', e.target.value)}
            className="select"
          >
            <option value="">All templates</option>
            {categories.templates.map((item) => (
              <option key={item.value} value={item.value}>
                {item.display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Main Spirit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Main Spirit
          </label>
          <select
            value={filters.main_spirit || ''}
            onChange={(e) => updateFilter('main_spirit', e.target.value)}
            className="select"
          >
            <option value="">All spirits</option>
            {categories.spirits.map((item) => (
              <option key={item.value} value={item.value}>
                {item.display_name}
              </option>
            ))}
          </select>
        </div>

        {/* Glassware */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Glassware
          </label>
          <select
            value={filters.glassware || ''}
            onChange={(e) => updateFilter('glassware', e.target.value)}
            className="select"
          >
            <option value="">All glassware</option>
            {categories.glassware.map((group) => (
              <optgroup key={group.name} label={group.name}>
                {group.items.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.display_name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Serving Style */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Serving Style
          </label>
          <select
            value={filters.serving_style || ''}
            onChange={(e) => updateFilter('serving_style', e.target.value)}
            className="select"
          >
            <option value="">All styles</option>
            {categories.serving_styles.map((item) => (
              <option key={item.value} value={item.value}>
                {item.display_name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
