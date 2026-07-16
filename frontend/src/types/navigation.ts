/** 创作者导航类型定义 */

export interface NavigationTaskItem {
  task_key: string
  category: string
  title: string
  description: string | null
  priority: number
  is_checked: boolean
}

export interface NavigationStatusResult {
  active_path: string
  progress_percent: number
  current_task: NavigationTaskItem | null
  completed_tasks: NavigationTaskItem[]
  remaining_tasks: NavigationTaskItem[]
  last_completed_at: string | null
}

export interface CompleteTaskResult {
  status: string
  task_key: string
  new_progress: number
  next_task: NavigationTaskItem | null
}
