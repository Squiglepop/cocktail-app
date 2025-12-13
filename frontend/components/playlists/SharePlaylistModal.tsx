'use client';

import { useState, useEffect } from 'react';
import {
  CollectionShare,
  fetchCollectionShares,
  shareCollection,
  updateCollectionShare,
  removeCollectionShare,
} from '@/lib/api';
import { X, UserPlus, Trash2, Loader2, Users, Pencil, Eye } from 'lucide-react';

interface SharePlaylistModalProps {
  playlistId: string;
  playlistName: string;
  token: string | null;
  onClose: () => void;
}

export function SharePlaylistModal({
  playlistId,
  playlistName,
  token,
  onClose,
}: SharePlaylistModalProps) {
  const [shares, setShares] = useState<CollectionShare[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [canEdit, setCanEdit] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [error, setError] = useState('');
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    fetchCollectionShares(playlistId, token)
      .then(setShares)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [playlistId, token]);

  const handleShare = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;

    setSharing(true);
    setError('');

    try {
      const newShare = await shareCollection(playlistId, email.trim(), canEdit, token);
      setShares([newShare, ...shares]);
      setEmail('');
      setCanEdit(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to share');
    } finally {
      setSharing(false);
    }
  };

  const handleToggleEdit = async (share: CollectionShare) => {
    setUpdatingId(share.id);
    try {
      const updated = await updateCollectionShare(playlistId, share.id, !share.can_edit, token);
      setShares(shares.map((s) => (s.id === share.id ? updated : s)));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update permission');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleRemoveShare = async (shareId: string) => {
    setRemovingId(shareId);
    try {
      await removeCollectionShare(playlistId, shareId, token);
      setShares(shares.filter((s) => s.id !== shareId));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to remove share');
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-amber-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Share Playlist
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Share form */}
        <form onSubmit={handleShare} className="p-4 border-b border-gray-100">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Share "{playlistName}" with:
          </label>
          <div className="flex gap-2">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              className="input flex-1"
              disabled={sharing}
            />
            <button
              type="submit"
              disabled={sharing || !email.trim()}
              className="btn btn-primary"
            >
              {sharing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
            </button>
          </div>
          {/* Permission checkbox */}
          <label className="flex items-center gap-2 mt-3 cursor-pointer">
            <input
              type="checkbox"
              checked={canEdit}
              onChange={(e) => setCanEdit(e.target.checked)}
              className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
              disabled={sharing}
            />
            <span className="text-sm text-gray-600">
              Allow editing (add, remove, reorder recipes)
            </span>
          </label>
          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}
        </form>

        {/* Shares list */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : shares.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="h-10 w-10 text-gray-300 mx-auto mb-2" />
              <p>Not shared with anyone yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-gray-500 mb-3">
                Shared with {shares.length} {shares.length === 1 ? 'person' : 'people'}
              </p>
              {shares.map((share) => (
                <div
                  key={share.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 truncate">
                      {share.shared_with_display_name || share.shared_with_email}
                    </p>
                    {share.shared_with_display_name && (
                      <p className="text-sm text-gray-500 truncate">
                        {share.shared_with_email}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-1 ml-2">
                    {/* Edit permission toggle */}
                    <button
                      onClick={() => handleToggleEdit(share)}
                      disabled={updatingId === share.id}
                      className={`p-1.5 rounded ${
                        share.can_edit
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-gray-200 text-gray-500'
                      } hover:opacity-80`}
                      title={share.can_edit ? 'Can edit - click to make view only' : 'View only - click to allow editing'}
                    >
                      {updatingId === share.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : share.can_edit ? (
                        <Pencil className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                    {/* Remove button */}
                    <button
                      onClick={() => handleRemoveShare(share.id)}
                      disabled={removingId === share.id}
                      className="p-1.5 text-gray-400 hover:text-red-600"
                      title="Remove access"
                    >
                      {removingId === share.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="btn btn-secondary w-full"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
