'use client';

import { useEffect, useState, useRef } from 'react';
import { Categories, CategoryItem, CategoryGroup, fetchCategories } from '@/lib/api';
import { X, ChevronDown, ChevronUp, SlidersHorizontal, Heart } from 'lucide-react';
import { useFavourites } from '@/lib/favourites-context';

interface FilterSidebarProps {
  filters: {
    template?: string;
    main_spirit?: string;
    glassware?: string;
    serving_style?: string;
    search?: string;
    min_rating?: string;
    favourites_only?: string;
  };
  onFilterChange: (filters: FilterSidebarProps['filters']) => void;
  className?: string;
  variant?: 'sidebar' | 'tile';
}

export function FilterSidebar({ filters, onFilterChange, className = '', variant = 'sidebar' }: FilterSidebarProps) {
  const [categories, setCategories] = useState<Categories | null>(null);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { favouriteCount } = useFavourites();

  // Close dropdown when clicking outside
  useEffect(() => {
    if (variant !== 'tile' || !isExpanded) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [variant, isExpanded]);

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
  const activeFilterCount = Object.values(filters).filter(v => v).length;

  // Tile variant for mobile
  if (variant === 'tile') {
    return (
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="card p-3 flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow w-full h-full bg-amber-50 border-amber-200"
        >
          <div className="relative">
            <SlidersHorizontal className="h-6 w-6 text-amber-700 mb-1" />
            {activeFilterCount > 0 && (
              <span className="absolute -top-1 -right-2 bg-amber-600 text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </div>
          <span className="text-xs font-medium text-amber-800">Filters</span>
        </button>

        {/* Dropdown */}
        {isExpanded && categories && (
          <div className="absolute top-full right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 p-4 space-y-4 z-[60]">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Filters</h3>
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

            {/* Favourites toggle */}
            <button
              onClick={() => updateFilter('favourites_only', filters.favourites_only ? '' : 'true')}
              className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
                filters.favourites_only
                  ? 'bg-red-50 border-red-200 text-red-700'
                  : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
              }`}
            >
              <Heart className={`h-4 w-4 ${filters.favourites_only ? 'fill-red-500 text-red-500' : ''}`} />
              <span className="text-sm font-medium">Favourites only</span>
              {favouriteCount > 0 && (
                <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${
                  filters.favourites_only ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-600'
                }`}>
                  {favouriteCount}
                </span>
              )}
            </button>

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

            {/* Min Rating */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                My Rating
              </label>
              <select
                value={filters.min_rating || ''}
                onChange={(e) => updateFilter('min_rating', e.target.value)}
                className="select"
              >
                <option value="">Any rating</option>
                <option value="5">5 stars</option>
                <option value="4">4+ stars</option>
                <option value="3">3+ stars</option>
                <option value="2">2+ stars</option>
                <option value="1">1+ stars</option>
              </select>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Sidebar variant (default)
  if (loading) {
    return (
      <div className={className}>
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
    <div className={className}>
      <div className="card p-4 space-y-6">
        {/* Header */}
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

        {/* Filter content */}
        <div className="space-y-6">
          {/* Favourites toggle */}
          <button
            onClick={() => updateFilter('favourites_only', filters.favourites_only ? '' : 'true')}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
              filters.favourites_only
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-gray-50 border-gray-200 text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Heart className={`h-4 w-4 ${filters.favourites_only ? 'fill-red-500 text-red-500' : ''}`} />
            <span className="text-sm font-medium">Favourites only</span>
            {favouriteCount > 0 && (
              <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${
                filters.favourites_only ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-600'
              }`}>
                {favouriteCount}
              </span>
            )}
          </button>

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

          {/* Min Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              My Rating
            </label>
            <select
              value={filters.min_rating || ''}
              onChange={(e) => updateFilter('min_rating', e.target.value)}
              className="select"
            >
              <option value="">Any rating</option>
              <option value="5">5 stars</option>
              <option value="4">4+ stars</option>
              <option value="3">3+ stars</option>
              <option value="2">2+ stars</option>
              <option value="1">1+ stars</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
