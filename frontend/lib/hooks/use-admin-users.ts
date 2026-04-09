'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAdminUsers, updateUserStatus, UserStatusUpdate } from '@/lib/api';
import { queryKeys } from '@/lib/query-client';

export function useAdminUsers(
  params: { page?: number; per_page?: number; search?: string; status?: string },
  token: string | null
) {
  return useQuery({
    queryKey: queryKeys.adminUsers.list(params),
    queryFn: () => fetchAdminUsers(params, token),
    staleTime: 60_000,
    enabled: !!token,
  });
}

export function useUpdateUserStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data, token }: { id: string; data: UserStatusUpdate; token: string | null }) =>
      updateUserStatus(id, data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminUsers.all });
    },
  });
}
