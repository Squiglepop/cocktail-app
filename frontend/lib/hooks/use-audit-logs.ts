'use client';

import { useQuery } from '@tanstack/react-query';
import { fetchAuditLogs } from '@/lib/api';
import { queryKeys } from '@/lib/query-client';

export function useAuditLogs(
  params: {
    action?: string;
    entity_type?: string;
    from?: string;
    to?: string;
    page?: number;
    per_page?: number;
  },
  token: string | null
) {
  return useQuery({
    queryKey: queryKeys.auditLogs.list(params),
    queryFn: () => fetchAuditLogs(params, token),
    enabled: !!token,
    staleTime: 60_000,
  });
}
