'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AdminCategoryCreate, AdminCategoryUpdate,
  fetchAdminCategories, createAdminCategory, updateAdminCategory,
  deleteAdminCategory, reorderAdminCategories,
} from '@/lib/api';
import { queryKeys, STALE_TIMES } from '@/lib/query-client';

export function useAdminCategories(type: string, token: string | null) {
  return useQuery({
    queryKey: queryKeys.adminCategories.byType(type),
    queryFn: () => fetchAdminCategories(type, token),
    staleTime: STALE_TIMES.adminCategories,
    enabled: !!token,
  });
}

export function useCreateCategory(type: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ data, token }: { data: AdminCategoryCreate; token: string | null }) =>
      createAdminCategory(type, data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
    },
  });
}

export function useUpdateCategory(type: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data, token }: { id: string; data: AdminCategoryUpdate; token: string | null }) =>
      updateAdminCategory(type, id, data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
    },
  });
}

export function useDeleteCategory(type: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, token }: { id: string; token: string | null }) =>
      deleteAdminCategory(type, id, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
    },
  });
}

export function useReorderCategories(type: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ids, token }: { ids: string[]; token: string | null }) =>
      reorderAdminCategories(type, ids, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminCategories.byType(type) });
    },
  });
}
