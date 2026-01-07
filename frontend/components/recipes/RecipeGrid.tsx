'use client';

import { useCallback, useEffect, useRef, useState, CSSProperties, ReactElement } from 'react';
import { Grid, GridImperativeAPI } from 'react-window';
import { RecipeListItem } from '@/lib/api';
import { RecipeCard } from './RecipeCard';
import { GlassWater, Loader2 } from 'lucide-react';

interface RecipeGridProps {
  recipes: RecipeListItem[];
  loading?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
}

// Constants for grid layout
const GAP = 16; // gap-4 = 16px
const GAP_LG = 24; // gap-6 = 24px
const INFO_STRIP_HEIGHT = 56; // Bottom info strip with badges + uploader
const OVERSCAN_COUNT = 2;

// Cell props type for react-window v2
interface CellProps {
  recipes: RecipeListItem[];
  columnCount: number;
  gap: number;
}

// Cell component for react-window v2
function RecipeCell({
  columnIndex,
  rowIndex,
  style,
  recipes,
  columnCount,
  gap,
}: {
  ariaAttributes: { 'aria-colindex': number; role: 'gridcell' };
  columnIndex: number;
  rowIndex: number;
  style: CSSProperties;
} & CellProps): ReactElement {
  const recipeIndex = rowIndex * columnCount + columnIndex;

  if (recipeIndex >= recipes.length) {
    return <div style={style} />;
  }

  const recipe = recipes[recipeIndex];

  // Adjust style to account for gaps
  const adjustedStyle: CSSProperties = {
    ...style,
    left: Number(style.left) + gap * columnIndex,
    top: Number(style.top) + gap * rowIndex,
    width: Number(style.width) - gap,
    height: Number(style.height) - gap,
    padding: 0,
  };

  return (
    <div style={adjustedStyle}>
      <RecipeCard recipe={recipe} />
    </div>
  );
}

export function RecipeGrid({ recipes, loading, loadingMore, onLoadMore }: RecipeGridProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gridRef = useRef<GridImperativeAPI | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [isDesktop, setIsDesktop] = useState(false);

  // Update dimensions on resize AND when returning from navigation (Android back button fix)
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: window.innerHeight - rect.top - 100 });
        setIsDesktop(window.innerWidth >= 1024); // lg breakpoint
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    // Re-measure when page becomes visible again (Android back navigation)
    document.addEventListener('visibilitychange', updateDimensions);
    window.addEventListener('focus', updateDimensions);
    // Also re-measure on popstate (back/forward navigation)
    window.addEventListener('popstate', updateDimensions);

    return () => {
      window.removeEventListener('resize', updateDimensions);
      document.removeEventListener('visibilitychange', updateDimensions);
      window.removeEventListener('focus', updateDimensions);
      window.removeEventListener('popstate', updateDimensions);
    };
  }, []);

  // Calculate grid parameters based on screen size
  const columnCount = isDesktop ? 3 : 2;
  const gap = isDesktop ? GAP_LG : GAP;
  const rowCount = Math.ceil(recipes.length / columnCount);
  // Account for mobile scrollbar overlay (16px on mobile)
  const scrollbarPadding = isDesktop ? 0 : 16;
  const gridWidth = dimensions.width - scrollbarPadding;
  // Grid column width = columnWidth + gap (each column includes trailing gap)
  // Total = columnCount * (columnWidth + gap) must equal gridWidth
  // So: columnWidth = gridWidth / columnCount - gap
  const columnWidth = gridWidth > 0
    ? (gridWidth / columnCount) - gap
    : 200;
  // Calculate row height dynamically: 3:4 aspect image + info strip
  // This ensures cards fit exactly without whitespace
  const rowHeight = Math.ceil((columnWidth * 4 / 3) + INFO_STRIP_HEIGHT);

  // Handle scroll to trigger load more
  const handleCellsRendered = useCallback((
    _visibleCells: { columnStartIndex: number; columnStopIndex: number; rowStartIndex: number; rowStopIndex: number },
    allCells: { columnStartIndex: number; columnStopIndex: number; rowStartIndex: number; rowStopIndex: number }
  ) => {
    // When we're within 2 rows of the end, trigger load more
    if (onLoadMore && allCells.rowStopIndex >= rowCount - 2) {
      onLoadMore();
    }
  }, [onLoadMore, rowCount]);

  // Reset scroll position when recipes change significantly (e.g., filter change)
  const prevRecipesLengthRef = useRef(recipes.length);
  useEffect(() => {
    // If recipes reduced significantly, we likely filtered - reset scroll
    if (recipes.length < prevRecipesLengthRef.current / 2 && gridRef.current) {
      gridRef.current.scrollToRow({ index: 0 });
    }
    prevRecipesLengthRef.current = recipes.length;
  }, [recipes.length]);

  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card animate-pulse overflow-hidden">
            <div className="aspect-[3/4] bg-gray-200 rounded-t-lg"></div>
            <div className="p-2 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (recipes.length === 0) {
    return (
      <div className="text-center py-12">
        <GlassWater className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No recipes found
        </h3>
        <p className="text-gray-500">
          Try adjusting your filters or upload a new recipe screenshot.
        </p>
      </div>
    );
  }

  // Calculate total grid height including gaps
  const totalHeight = rowCount * (rowHeight + gap);

  // Ensure minimum height for the grid
  const gridHeight = Math.max(400, Math.min(dimensions.height || 600, totalHeight + 50));

  return (
    <div ref={containerRef} className="w-full min-h-[400px]">
      {dimensions.width > 0 ? (
        <>
          <Grid
            gridRef={gridRef}
            className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
            columnCount={columnCount}
            columnWidth={columnWidth + gap}
            rowCount={rowCount}
            rowHeight={rowHeight + gap}
            overscanCount={OVERSCAN_COUNT}
            cellComponent={RecipeCell}
            cellProps={{ recipes, columnCount, gap }}
            onCellsRendered={handleCellsRendered}
            style={{
              height: gridHeight,
              width: gridWidth,
              overflowX: 'hidden',
            }}
          />
          {loadingMore && (
            <div className="flex justify-center py-6">
              <Loader2 className="h-6 w-6 animate-spin text-amber-600" />
            </div>
          )}
        </>
      ) : (
        // Fallback while measuring - show regular grid
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {recipes.map((recipe) => (
            <RecipeCard key={recipe.id} recipe={recipe} />
          ))}
        </div>
      )}
    </div>
  );
}
