import { request } from '@/api/client'
import type { NavigationStatusResult, CompleteTaskResult } from '@/types/navigation'

export function getNavigationStatus(userId: string, path = 'onboarding') {
  return request.get(`/navigation/status/${userId}?path=${path}`).then(res => res.data as NavigationStatusResult)
}

export function completeTask(taskKey: string): Promise<CompleteTaskResult> {
  return request.post(`/navigation/complete/${taskKey}`).then(res => res.data)
}

export function listTasks(category = 'onboarding') {
  return request.get(`/navigation/tasks?category=${category}`).then(res => res.data)
}

export function switchPath(path: string) {
  return request.post('/navigation/switch-path', { path }).then(res => res.data)
}
