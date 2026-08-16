import type { OperationCooperation, OperationScope } from '~/types/operation'

function getApiBase(): string {
  return useRuntimeConfig().public.apiBase
}

function authHeaders(): Record<string, string> {
  const token = import.meta.client ? localStorage.getItem('orispark-token') : useCookie('orispark-token').value
  if (!token) throw new Error('未登录')
  return { Authorization: `Bearer ${token}` }
}

export function fetchOperatorOperations(status?: string): Promise<OperationCooperation[]> {
  const query = new URLSearchParams().toString()
  const url = `${getApiBase()}/operator/operations${query ? '?' + query : ''}`
  return $fetch(url, { headers: authHeaders() })
}

export function proposeCooperation(data: { work_id: string; scope: OperationScope; notes?: string }): Promise<OperationCooperation> {
  return $fetch(`${getApiBase()}/operator/operations/propose`, {
    method: 'POST',
    headers: authHeaders(),
    body: data,
  })
}

export function fetchCreatorPendingOperations(): Promise<OperationCooperation[]> {
  return $fetch(`${getApiBase()}/operator/operations/creator/pending`, {
    headers: authHeaders(),
  })
}

export function acceptCooperation(id: string): Promise<{ id: string; status: string; message?: string }> {
  return $fetch(`${getApiBase()}/operator/operations/creator/accept/${id}`, {
    method: 'POST',
    headers: authHeaders(),
  })
}

export function rejectCooperation(id: string): Promise<{ id: string; status: string }> {
  return $fetch(`${getApiBase()}/operator/operations/creator/reject/${id}`, {
    method: 'POST',
    headers: authHeaders(),
  })
}

export function fetchWorkPublic(id: string): Promise<{ id: string; title: string; creator_name: string; category: string } | null> {
  return $fetch(`${getApiBase()}/public/works/${id}`).catch(() => null)
}
