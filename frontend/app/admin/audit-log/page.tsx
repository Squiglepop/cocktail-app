'use client';

import { Fragment, useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { useAuditLogs } from '@/lib/hooks';
import { formatEnumValue } from '@/lib/api';
import { clsx } from 'clsx';

const ACTION_OPTIONS = [
  'category_create', 'category_update', 'category_delete',
  'ingredient_create', 'ingredient_update', 'ingredient_delete', 'ingredient_merge',
  'recipe_admin_update', 'recipe_admin_delete',
  'user_activate', 'user_deactivate', 'user_grant_admin', 'user_revoke_admin',
];

const ENTITY_TYPE_OPTIONS = [
  'category', 'ingredient', 'recipe', 'user',
];

export default function AuditLogPage() {
  const { token } = useAuth();
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [expandedRowId, setExpandedRowId] = useState<string | null>(null);

  const { data, isLoading, error } = useAuditLogs(
    {
      action: actionFilter || undefined,
      entity_type: entityTypeFilter || undefined,
      from: fromDate || undefined,
      to: toDate || undefined,
      page,
      per_page: 20,
    },
    token
  );

  function handleFilterChange(setter: (value: string) => void, value: string) {
    setter(value);
    setPage(1);
  }

  function clearFilters() {
    setActionFilter('');
    setEntityTypeFilter('');
    setFromDate('');
    setToDate('');
    setPage(1);
  }

  function toggleRow(id: string) {
    setExpandedRowId(prev => prev === id ? null : id);
  }

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Audit Log</h1>

      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label htmlFor="action-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Action
          </label>
          <select
            id="action-filter"
            value={actionFilter}
            onChange={e => handleFilterChange(setActionFilter, e.target.value)}
            className="block w-48 rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
          >
            <option value="">All Actions</option>
            {ACTION_OPTIONS.map(action => (
              <option key={action} value={action}>{formatEnumValue(action)}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="entity-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Entity Type
          </label>
          <select
            id="entity-filter"
            value={entityTypeFilter}
            onChange={e => handleFilterChange(setEntityTypeFilter, e.target.value)}
            className="block w-48 rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
          >
            <option value="">All Entities</option>
            {ENTITY_TYPE_OPTIONS.map(entity => (
              <option key={entity} value={entity}>{formatEnumValue(entity)}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="from-date" className="block text-sm font-medium text-gray-700 mb-1">
            From
          </label>
          <input
            id="from-date"
            type="date"
            value={fromDate}
            onChange={e => handleFilterChange(setFromDate, e.target.value)}
            className="block rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
          />
        </div>

        <div>
          <label htmlFor="to-date" className="block text-sm font-medium text-gray-700 mb-1">
            To
          </label>
          <input
            id="to-date"
            type="date"
            value={toDate}
            onChange={e => handleFilterChange(setToDate, e.target.value)}
            className="block rounded-md border-gray-300 shadow-sm focus:border-amber-500 focus:ring-amber-500 text-sm"
          />
        </div>

        <button
          onClick={clearFilters}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Clear Filters
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md mb-4">
          Failed to load audit logs. Please try again.
        </div>
      )}

      {/* Table */}
      {data && (
        <>
          <div className="overflow-x-auto border border-gray-200 rounded-lg">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity ID</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.items.map(entry => (
                  <Fragment key={entry.id}>
                    <tr
                      onClick={() => toggleRow(entry.id)}
                      className={clsx(
                        'cursor-pointer hover:bg-gray-50 transition-colors',
                        expandedRowId === entry.id && 'bg-amber-50'
                      )}
                    >
                      <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                        {new Date(entry.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {entry.admin_email ?? entry.admin_user_id}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {formatEnumValue(entry.action)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {formatEnumValue(entry.entity_type)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500 font-mono">
                        {entry.entity_id ? (entry.entity_id.length > 8 ? `${entry.entity_id.substring(0, 8)}...` : entry.entity_id) : '—'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-400">
                        {entry.details ? (expandedRowId === entry.id ? '▼' : '▶') : '—'}
                      </td>
                    </tr>
                    {expandedRowId === entry.id && entry.details && (
                      <tr>
                        <td colSpan={6} className="bg-gray-50 px-6 py-4">
                          <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">{JSON.stringify(entry.details, null, 2)}</pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                      No audit log entries found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <span className="text-sm text-gray-700">
              {data.total} total {data.total === 1 ? 'entry' : 'entries'}
            </span>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="text-sm text-gray-700">
                Page {page} of {totalPages || 1}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page >= totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
