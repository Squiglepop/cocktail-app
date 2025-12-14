'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import {
  CollectionDetail,
  CollectionRecipe,
  fetchCollection,
  updateCollection,
  deleteCollection,
  removeRecipeFromCollection,
  reorderCollectionRecipes,
  formatEnumValue,
  getRecipeImageUrl,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { SharePlaylistModal } from '@/components/playlists/SharePlaylistModal';
import {
  ArrowLeft,
  GlassWater,
  ListMusic,
  Trash2,
  X,
  GripVertical,
  Pencil,
  Check,
  Lock,
  Globe,
  Share2,
} from 'lucide-react';

export default function PlaylistDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user, token } = useAuth();
  const [playlist, setPlaylist] = useState<CollectionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editingDescription, setEditingDescription] = useState(false);
  const [tempName, setTempName] = useState('');
  const [tempDescription, setTempDescription] = useState('');
  const [draggedItem, setDraggedItem] = useState<CollectionRecipe | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);

  const isOwner = user && playlist && playlist.user_id === user.id;
  const canEdit = playlist?.can_edit ?? isOwner;

  useEffect(() => {
    if (params.id) {
      fetchCollection(params.id as string, token)
        .then(setPlaylist)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [params.id, token]);

  const handleDelete = async () => {
    if (!playlist) return;
    if (!confirm('Are you sure you want to delete this playlist?')) return;

    setDeleting(true);
    try {
      await deleteCollection(playlist.id, token);
      router.push('/playlists');
    } catch (error) {
      console.error('Failed to delete:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete playlist');
      setDeleting(false);
    }
  };

  const handleRemoveRecipe = async (recipeId: string) => {
    if (!playlist) return;

    try {
      await removeRecipeFromCollection(playlist.id, recipeId, token);
      setPlaylist({
        ...playlist,
        recipes: playlist.recipes.filter((r) => r.recipe_id !== recipeId),
        recipe_count: playlist.recipe_count - 1,
      });
    } catch (error) {
      console.error('Failed to remove recipe:', error);
      alert(error instanceof Error ? error.message : 'Failed to remove recipe');
    }
  };

  const handleSaveName = async () => {
    if (!playlist || !tempName.trim()) return;

    try {
      await updateCollection(playlist.id, { name: tempName.trim() }, token);
      setPlaylist({ ...playlist, name: tempName.trim() });
      setEditingName(false);
    } catch (error) {
      console.error('Failed to update name:', error);
      alert(error instanceof Error ? error.message : 'Failed to update name');
    }
  };

  const handleSaveDescription = async () => {
    if (!playlist) return;

    try {
      await updateCollection(
        playlist.id,
        { description: tempDescription.trim() || undefined },
        token
      );
      setPlaylist({ ...playlist, description: tempDescription.trim() || undefined });
      setEditingDescription(false);
    } catch (error) {
      console.error('Failed to update description:', error);
      alert(error instanceof Error ? error.message : 'Failed to update description');
    }
  };

  const handleTogglePublic = async () => {
    if (!playlist) return;

    try {
      await updateCollection(playlist.id, { is_public: !playlist.is_public }, token);
      setPlaylist({ ...playlist, is_public: !playlist.is_public });
    } catch (error) {
      console.error('Failed to update visibility:', error);
      alert(error instanceof Error ? error.message : 'Failed to update visibility');
    }
  };

  // Drag and drop handlers
  const handleDragStart = useCallback((e: React.DragEvent, recipe: CollectionRecipe) => {
    setDraggedItem(recipe);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault();
    setDragOverIndex(index);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedItem(null);
    setDragOverIndex(null);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent, targetIndex: number) => {
    e.preventDefault();
    if (!playlist || !draggedItem) return;

    const recipes = [...playlist.recipes];
    const draggedIndex = recipes.findIndex((r) => r.recipe_id === draggedItem.recipe_id);

    if (draggedIndex === targetIndex) {
      setDraggedItem(null);
      setDragOverIndex(null);
      return;
    }

    // Remove and insert at new position
    recipes.splice(draggedIndex, 1);
    recipes.splice(targetIndex, 0, draggedItem);

    // Update positions
    const reorderedRecipes = recipes.map((r, i) => ({ ...r, position: i }));

    setPlaylist({ ...playlist, recipes: reorderedRecipes });
    setDraggedItem(null);
    setDragOverIndex(null);

    // Save to backend
    try {
      await reorderCollectionRecipes(
        playlist.id,
        reorderedRecipes.map((r) => ({ recipe_id: r.recipe_id, position: r.position })),
        token
      );
    } catch (error) {
      console.error('Failed to reorder:', error);
      // Refetch to reset order
      fetchCollection(playlist.id, token).then(setPlaylist);
    }
  }, [playlist, draggedItem, token]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-8">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-12 bg-gray-200 rounded w-1/2"></div>
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <div className="w-24 h-18 bg-gray-200 rounded"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-5 bg-gray-200 rounded w-1/2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <ListMusic className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Playlist not found
          </h2>
          <Link href="/playlists" className="text-amber-600 hover:text-amber-700">
            Back to playlists
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        href="/playlists"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to playlists
      </Link>

      {/* Playlist Header */}
      <div className="space-y-4 mb-8">
        {/* Name */}
        <div className="flex items-center gap-3">
          <ListMusic className="h-8 w-8 text-amber-600 flex-shrink-0" />
          {editingName && isOwner ? (
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                value={tempName}
                onChange={(e) => setTempName(e.target.value)}
                className="input text-2xl font-bold"
                autoFocus
              />
              <button
                onClick={handleSaveName}
                className="btn btn-ghost text-green-600"
              >
                <Check className="h-5 w-5" />
              </button>
              <button
                onClick={() => setEditingName(false)}
                className="btn btn-ghost text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              {playlist.name}
              {isOwner && (
                <button
                  onClick={() => {
                    setTempName(playlist.name);
                    setEditingName(true);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <Pencil className="h-4 w-4" />
                </button>
              )}
            </h1>
          )}
        </div>

        {/* Description */}
        <div>
          {editingDescription && isOwner ? (
            <div className="flex items-start gap-2">
              <textarea
                value={tempDescription}
                onChange={(e) => setTempDescription(e.target.value)}
                className="input min-h-[60px] flex-1"
                placeholder="Add a description..."
                autoFocus
              />
              <button
                onClick={handleSaveDescription}
                className="btn btn-ghost text-green-600"
              >
                <Check className="h-5 w-5" />
              </button>
              <button
                onClick={() => setEditingDescription(false)}
                className="btn btn-ghost text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          ) : (
            <p
              className={`text-gray-600 ${isOwner ? 'cursor-pointer hover:text-gray-900' : ''}`}
              onClick={() => {
                if (isOwner) {
                  setTempDescription(playlist.description || '');
                  setEditingDescription(true);
                }
              }}
            >
              {playlist.description || (isOwner ? 'Add a description...' : '')}
            </p>
          )}
        </div>

        {/* Meta info and actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 text-sm text-gray-500">
            <span>
              {playlist.recipe_count} {playlist.recipe_count === 1 ? 'recipe' : 'recipes'}
            </span>
            {isOwner && (
              <button
                onClick={handleTogglePublic}
                className="flex items-center gap-1 hover:text-gray-700"
              >
                {playlist.is_public ? (
                  <>
                    <Globe className="h-4 w-4" />
                    Public
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4" />
                    Private
                  </>
                )}
              </button>
            )}
          </div>
          {isOwner && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowShareModal(true)}
                className="btn btn-secondary"
              >
                <Share2 className="h-4 w-4 mr-2" />
                Share
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="btn btn-ghost text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Share Modal */}
      {showShareModal && playlist && (
        <SharePlaylistModal
          playlistId={playlist.id}
          playlistName={playlist.name}
          token={token}
          onClose={() => setShowShareModal(false)}
        />
      )}

      {/* Recipes List */}
      {playlist.recipes.length === 0 ? (
        <div className="text-center py-12 border-2 border-dashed border-gray-200 rounded-lg">
          <GlassWater className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No recipes yet
          </h3>
          <p className="text-gray-500 mb-4">
            Add recipes from your library to this playlist.
          </p>
          <Link href="/" className="btn btn-primary">
            Browse Recipes
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {playlist.recipes.map((recipe, index) => (
            <div
              key={recipe.id}
              draggable={!!canEdit}
              onDragStart={(e) => handleDragStart(e, recipe)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragEnd={handleDragEnd}
              onDrop={(e) => handleDrop(e, index)}
              className={`
                flex items-center gap-4 p-3 rounded-lg border bg-white
                ${dragOverIndex === index ? 'border-amber-400 bg-amber-50' : 'border-gray-200'}
                ${draggedItem?.recipe_id === recipe.recipe_id ? 'opacity-50' : ''}
                ${canEdit ? 'cursor-move' : ''}
                group
              `}
            >
              {canEdit && (
                <GripVertical className="h-5 w-5 text-gray-400 flex-shrink-0" />
              )}

              <Link
                href={`/recipes/${recipe.recipe_id}`}
                className="flex items-center gap-4 flex-1 min-w-0"
              >
                {/* Thumbnail */}
                <div className="w-16 h-12 bg-gradient-to-br from-amber-100 to-amber-50 rounded flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                  {recipe.recipe_has_image ? (
                    <Image
                      src={getRecipeImageUrl(recipe.recipe_id)}
                      alt={recipe.recipe_name}
                      fill
                      sizes="64px"
                      className="object-cover"
                      loading="lazy"
                    />
                  ) : (
                    <GlassWater className="h-6 w-6 text-amber-300" />
                  )}
                </div>

                {/* Recipe info */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">
                    {recipe.recipe_name}
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    {recipe.recipe_template && (
                      <span>{formatEnumValue(recipe.recipe_template)}</span>
                    )}
                    {recipe.recipe_template && recipe.recipe_main_spirit && (
                      <span className="text-gray-300">|</span>
                    )}
                    {recipe.recipe_main_spirit && (
                      <span>{formatEnumValue(recipe.recipe_main_spirit)}</span>
                    )}
                  </div>
                </div>
              </Link>

              {/* Remove button */}
              {canEdit && (
                <button
                  onClick={() => handleRemoveRecipe(recipe.recipe_id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 transition-opacity"
                  title="Remove from playlist"
                >
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
