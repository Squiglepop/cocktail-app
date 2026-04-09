'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useAdminUsers, useUpdateUserStatus } from '@/lib/hooks';
import { AdminUser } from '@/lib/api';
import { clsx } from 'clsx';
import { Search, ChevronLeft, ChevronRight, Shield, ShieldOff, UserCheck, UserX, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react';

interface ConfirmAction {
  userId: string;
  userEmail: string;
  field: 'is_active' | 'is_admin';
  newValue: boolean;
}

export default function UsersPage() {
  const { user: currentUser, token } = useAuth();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading, error: queryError, refetch } = useAdminUsers(
    { page, per_page: 50, search: debouncedSearch || undefined, status: statusFilter || undefined },
    token
  );

  const updateStatus = useUpdateUserStatus();

  // Search debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  function handleToggle(user: AdminUser, field: 'is_active' | 'is_admin') {
    setError(null);
    if (user.id === currentUser?.id) {
      if (field === 'is_active') {
        setError('Cannot deactivate your own account');
      } else {
        setError('Cannot remove your own admin status');
      }
      return;
    }
    setConfirmAction({
      userId: user.id,
      userEmail: user.email,
      field,
      newValue: !user[field],
    });
  }

  async function handleConfirm() {
    if (!confirmAction) return;
    setError(null);
    try {
      await updateStatus.mutateAsync({
        id: confirmAction.userId,
        data: { [confirmAction.field]: confirmAction.newValue },
        token,
      });
      setConfirmAction(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
      setConfirmAction(null);
    }
  }

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 0;

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">User Management</h1>
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
        </div>
      </div>
    );
  }

  if (queryError) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">User Management</h1>
        <div className="text-center py-12" aria-live="polite">
          <p className="text-red-600 mb-4">Failed to load users</p>
          <button
            onClick={() => refetch()}
            className="btn bg-amber-600 text-white hover:bg-amber-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">User Management</h1>

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between" aria-live="polite">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-red-800 text-sm">{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-red-600 hover:text-red-800 text-sm font-medium">
            Dismiss
          </button>
        </div>
      )}

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by email or name..."
            aria-label="Search users"
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
          />
        </div>
        <div className="flex gap-2">
          {(['', 'active', 'inactive'] as const).map((status) => (
            <button
              key={status}
              onClick={() => { setStatusFilter(status); setPage(1); }}
              className={clsx(
                'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                statusFilter === status
                  ? 'bg-amber-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              {status === '' ? 'All' : status === 'active' ? 'Active' : 'Inactive'}
            </button>
          ))}
        </div>
      </div>

      {/* Empty state */}
      {data && data.items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg font-medium">No users found</p>
          <p className="text-sm mt-1">Try adjusting your search or filter</p>
        </div>
      ) : (
        <>
          {/* User table */}
          <div className="overflow-x-auto bg-white rounded-lg shadow">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Display Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Admin</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recipes</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {data?.items.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{user.email}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{user.display_name ?? '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        role="switch"
                        aria-checked={user.is_active}
                        aria-label={`Toggle active status for ${user.email}`}
                        onClick={() => handleToggle(user, 'is_active')}
                        className="inline-flex items-center"
                      >
                        <span
                          role="status"
                          className={clsx(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                            user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          )}
                        >
                          {user.is_active ? <UserCheck className="h-3 w-3" /> : <UserX className="h-3 w-3" />}
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        role="switch"
                        aria-checked={user.is_admin}
                        aria-label={`Toggle admin status for ${user.email}`}
                        onClick={() => handleToggle(user, 'is_admin')}
                        className="inline-flex items-center"
                      >
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                            user.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-600'
                          )}
                        >
                          {user.is_admin ? <Shield className="h-3 w-3" /> : <ShieldOff className="h-3 w-3" />}
                          {user.is_admin ? 'Admin' : 'User'}
                        </span>
                      </button>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{user.recipe_count}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {user.last_login_at ? new Date(user.last_login_at).toLocaleDateString() : 'Never'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages} ({data?.total} total)
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </>
      )}

      {/* Confirmation Modal */}
      {confirmAction && (
        <ConfirmActionModal
          confirmAction={confirmAction}
          onConfirm={handleConfirm}
          onCancel={() => setConfirmAction(null)}
          isLoading={updateStatus.isPending}
        />
      )}
    </div>
  );
}

function ConfirmActionModal({
  confirmAction,
  onConfirm,
  onCancel,
  isLoading,
}: {
  confirmAction: ConfirmAction;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading: boolean;
}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  const { field, newValue, userEmail } = confirmAction;

  let title: string;
  let variant: 'danger' | 'warning' | 'default';
  let confirmLabel: string;

  if (field === 'is_active') {
    if (newValue) {
      title = 'Activate this user?';
      variant = 'default';
      confirmLabel = 'Activate';
    } else {
      title = 'Deactivate this user?';
      variant = 'danger';
      confirmLabel = 'Deactivate';
    }
  } else {
    if (newValue) {
      title = `Grant admin privileges to ${userEmail}?`;
      variant = 'warning';
      confirmLabel = 'Grant Admin';
    } else {
      title = `Revoke admin privileges from ${userEmail}?`;
      variant = 'warning';
      confirmLabel = 'Revoke Admin';
    }
  }

  const confirmBtnClass = clsx(
    'px-4 py-2 rounded-lg text-sm font-medium text-white disabled:opacity-50',
    variant === 'danger' && 'bg-red-600 hover:bg-red-700',
    variant === 'warning' && 'bg-amber-600 hover:bg-amber-700',
    variant === 'default' && 'bg-green-600 hover:bg-green-700',
  );

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onCancel}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-sm w-full p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className={clsx(
            'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
            variant === 'danger' && 'bg-red-100',
            variant === 'warning' && 'bg-amber-100',
            variant === 'default' && 'bg-green-100',
          )}>
            {variant === 'default' ? (
              <CheckCircle className="h-5 w-5 text-green-600" />
            ) : (
              <AlertTriangle className={clsx(
                'h-5 w-5',
                variant === 'danger' && 'text-red-600',
                variant === 'warning' && 'text-amber-600',
              )} />
            )}
          </div>
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        </div>

        <p className="text-gray-600 mb-6 text-sm">
          {field === 'is_active' && !newValue && `This will prevent ${userEmail} from accessing the application.`}
          {field === 'is_active' && newValue && `This will restore ${userEmail}'s access to the application.`}
          {field === 'is_admin' && newValue && `This will give ${userEmail} full administrative privileges.`}
          {field === 'is_admin' && !newValue && `This will remove administrative privileges from ${userEmail}.`}
        </p>

        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={confirmBtnClass}
          >
            {isLoading ? (
              <span className="flex items-center gap-1">
                <Loader2 className="h-4 w-4 animate-spin" />
                Updating...
              </span>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
