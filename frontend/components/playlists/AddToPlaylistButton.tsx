'use client';

import { useState, useEffect, useRef } from 'react';
import {
  CollectionListItem,
  fetchCollections,
  addRecipeToCollection,
  removeRecipeFromCollection,
  createCollection,
} from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { Bookmark, Check, Plus, Loader2, X } from 'lucide-react';

interface AddToPlaylistButtonProps {
  recipeId: string;
  variant?: 'icon' | 'button';
  className?: string;
}

export function AddToPlaylistButton({
  recipeId,
  variant = 'icon',
  className = '',
}: AddToPlaylistButtonProps) {
  const { user, token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [playlists, setPlaylists] = useState<CollectionListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [recipeInPlaylists, setRecipeInPlaylists] = useState<Set<string>>(new Set());
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [creating, setCreating] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowCreateForm(false);
        setNewPlaylistName('');
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Fetch playlists when dropdown opens
  useEffect(() => {
    if (isOpen && token) {
      setLoading(true);
      fetchCollections(token)
        .then((collections) => {
          setPlaylists(collections);
          // We'd need an API to check which playlists contain this recipe
          // For now, we'll track it locally after actions
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [isOpen, token]);

  if (!user) {
    return null;
  }

  const handleToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleAddToPlaylist = async (playlistId: string) => {
    setActionLoading(playlistId);
    try {
      if (recipeInPlaylists.has(playlistId)) {
        await removeRecipeFromCollection(playlistId, recipeId, token);
        setRecipeInPlaylists((prev) => {
          const next = new Set(prev);
          next.delete(playlistId);
          return next;
        });
      } else {
        await addRecipeToCollection(playlistId, recipeId, token);
        setRecipeInPlaylists((prev) => new Set(prev).add(playlistId));
      }
    } catch (error) {
      console.error('Failed to update playlist:', error);
      alert(error instanceof Error ? error.message : 'Failed to update playlist');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreatePlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlaylistName.trim()) return;

    setCreating(true);
    try {
      console.log('[Playlist] Creating playlist:', newPlaylistName.trim(), 'for user:', user?.email);
      const newPlaylist = await createCollection(
        { name: newPlaylistName.trim() },
        token
      );
      console.log('[Playlist] Created:', newPlaylist, 'user_id:', newPlaylist.user_id);
      // Add recipe to the new playlist
      await addRecipeToCollection(newPlaylist.id, recipeId, token);
      console.log('[Playlist] Added recipe to playlist');

      setPlaylists([
        {
          id: newPlaylist.id,
          name: newPlaylist.name,
          description: newPlaylist.description,
          is_public: newPlaylist.is_public,
          recipe_count: 1,
          created_at: newPlaylist.created_at,
        },
        ...playlists,
      ]);
      setRecipeInPlaylists((prev) => new Set(prev).add(newPlaylist.id));
      setNewPlaylistName('');
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create playlist:', error);
      alert(error instanceof Error ? error.message : 'Failed to create playlist');
    } finally {
      setCreating(false);
    }
  };

  const isInAnyPlaylist = recipeInPlaylists.size > 0;

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {variant === 'icon' ? (
        <button
          onClick={handleToggle}
          className={`p-1.5 rounded-full transition-colors ${
            isInAnyPlaylist
              ? 'bg-amber-100 text-amber-600'
              : 'bg-white/80 text-gray-600 hover:bg-white hover:text-amber-600'
          }`}
          title="Add to playlist"
        >
          <Bookmark className={`h-4 w-4 ${isInAnyPlaylist ? 'fill-current' : ''}`} />
        </button>
      ) : (
        <button
          onClick={handleToggle}
          className="btn btn-secondary w-full justify-center"
        >
          <Bookmark className={`h-4 w-4 mr-1 ${isInAnyPlaylist ? 'fill-current text-amber-600' : ''}`} />
          <span className="hidden sm:inline">Add to </span>Playlist
        </button>
      )}

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50 overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-2 border-b border-gray-100">
            <h3 className="text-sm font-medium text-gray-900 px-2">
              Add to playlist
            </h3>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
              </div>
            ) : playlists.length === 0 && !showCreateForm ? (
              <div className="p-4 text-center text-sm text-gray-500">
                No playlists yet
              </div>
            ) : (
              <div className="py-1">
                {playlists.map((playlist) => (
                  <button
                    key={playlist.id}
                    onClick={() => handleAddToPlaylist(playlist.id)}
                    disabled={actionLoading === playlist.id}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    <div
                      className={`w-5 h-5 rounded border flex items-center justify-center flex-shrink-0 ${
                        recipeInPlaylists.has(playlist.id)
                          ? 'bg-amber-500 border-amber-500'
                          : 'border-gray-300'
                      }`}
                    >
                      {actionLoading === playlist.id ? (
                        <Loader2 className="h-3 w-3 animate-spin text-white" />
                      ) : recipeInPlaylists.has(playlist.id) ? (
                        <Check className="h-3 w-3 text-white" />
                      ) : null}
                    </div>
                    <span className="truncate">{playlist.name}</span>
                    <span className="text-xs text-gray-400 ml-auto flex-shrink-0">
                      {playlist.recipe_count}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="border-t border-gray-100">
            {showCreateForm ? (
              <form onSubmit={handleCreatePlaylist} className="p-2">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={newPlaylistName}
                    onChange={(e) => setNewPlaylistName(e.target.value)}
                    placeholder="Playlist name"
                    className="input text-sm flex-1"
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={creating || !newPlaylistName.trim()}
                    className="p-2 text-amber-600 hover:bg-amber-50 rounded disabled:opacity-50"
                  >
                    {creating ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Check className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewPlaylistName('');
                    }}
                    className="p-2 text-gray-400 hover:bg-gray-50 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setShowCreateForm(true)}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-amber-600 hover:bg-amber-50"
              >
                <Plus className="h-4 w-4" />
                Create new playlist
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
