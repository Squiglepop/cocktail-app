'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAdminIngredients, createAdminIngredient, updateAdminIngredient,
  deleteAdminIngredient, fetchDuplicateIngredients, mergeIngredients,
  AdminIngredientCreate, AdminIngredientUpdate, IngredientMergeRequest,
} from '@/lib/api';
import { queryKeys } from '@/lib/query-client';

export function useAdminIngredients(
  params: { page?: number; per_page?: number; search?: string; type?: string },
  token: string | null
) {
  return useQuery({
    queryKey: queryKeys.adminIngredients.list(params),
    queryFn: () => fetchAdminIngredients(params, token),
    staleTime: 60_000,
  });
}

export function useCreateIngredient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ data, token }: { data: AdminIngredientCreate; token: string | null }) =>
      createAdminIngredient(data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
    },
  });
}

export function useUpdateIngredient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data, token }: { id: string; data: AdminIngredientUpdate; token: string | null }) =>
      updateAdminIngredient(id, data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
    },
  });
}

export function useDeleteIngredient() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, token }: { id: string; token: string | null }) =>
      deleteAdminIngredient(id, token),
    onSuccess: (result) => {
      if (result.success) {
        queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
      }
    },
  });
}

export function useDuplicateDetection(token: string | null, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.adminIngredients.duplicates(),
    queryFn: () => fetchDuplicateIngredients(token),
    staleTime: 60_000,
    enabled,
  });
}

export function useMergeIngredients() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ data, token }: { data: IngredientMergeRequest; token: string | null }) =>
      mergeIngredients(data, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.adminIngredients.all });
    },
  });
}
