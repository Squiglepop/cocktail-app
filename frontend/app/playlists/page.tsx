'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  CollectionListItem,
  fetchCollections,
  createCollection,
} from '@/lib/api';
import { PlaylistCard } from '@/components/playlists/PlaylistCard';
import { useAuth } from '@/lib/auth-context';
import { ListMusic, Plus, ArrowLeft, X } from 'lucide-react';

export default function PlaylistsPage() {
  const router = useRouter();
  const { user, token, isLoading: authLoading } = useAuth();
  const [playlists, setPlaylists] = useState<CollectionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [newPlaylistDescription, setNewPlaylistDescription] = useState('');
  const [newPlaylistPublic, setNewPlaylistPublic] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }

    if (token) {
      fetchCollections(token)
        .then(setPlaylists)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [token, authLoading, user, router]);

  const handleCreatePlaylist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlaylistName.trim()) return;

    setCreating(true);
    setError('');

    try {
      const newPlaylist = await createCollection(
        {
          name: newPlaylistName.trim(),
          description: newPlaylistDescription.trim() || undefined,
          is_public: newPlaylistPublic,
        },
        token
      );
      setPlaylists([
        {
          id: newPlaylist.id,
          name: newPlaylist.name,
          description: newPlaylist.description,
          is_public: newPlaylist.is_public,
          recipe_count: 0,
          created_at: newPlaylist.created_at,
        },
        ...playlists,
      ]);
      setShowCreateModal(false);
      setNewPlaylistName('');
      setNewPlaylistDescription('');
      setNewPlaylistPublic(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create playlist');
    } finally {
      setCreating(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="aspect-[4/3] bg-gray-200 rounded-t-lg"></div>
              <div className="p-4 space-y-3">
                <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to recipes
        </Link>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ListMusic className="h-8 w-8 text-amber-600" />
            <h1 className="text-2xl font-bold text-gray-900">My Playlists</h1>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Playlist
          </button>
        </div>
      </div>

      {/* Playlists Grid */}
      {playlists.length === 0 ? (
        <div className="text-center py-12">
          <ListMusic className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No playlists yet
          </h3>
          <p className="text-gray-500 mb-4">
            Create your first playlist to organize your favorite recipes.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Playlist
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          {playlists.map((playlist) => (
            <PlaylistCard key={playlist.id} playlist={playlist} />
          ))}
        </div>
      )}

      {/* Create Playlist Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Create Playlist
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleCreatePlaylist} className="p-4 space-y-4">
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={newPlaylistName}
                  onChange={(e) => setNewPlaylistName(e.target.value)}
                  className="input"
                  placeholder="My Favorite Cocktails"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Description (optional)
                </label>
                <textarea
                  id="description"
                  value={newPlaylistDescription}
                  onChange={(e) => setNewPlaylistDescription(e.target.value)}
                  className="input min-h-[80px]"
                  placeholder="A collection of my go-to cocktails"
                  rows={3}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="public"
                  type="checkbox"
                  checked={newPlaylistPublic}
                  onChange={(e) => setNewPlaylistPublic(e.target.checked)}
                  className="h-4 w-4 text-amber-600 focus:ring-amber-500 border-gray-300 rounded"
                />
                <label
                  htmlFor="public"
                  className="text-sm text-gray-700"
                >
                  Make this playlist public
                </label>
              </div>

              {error && (
                <p className="text-sm text-red-600">{error}</p>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                  disabled={creating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={creating || !newPlaylistName.trim()}
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
