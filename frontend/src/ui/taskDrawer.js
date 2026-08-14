import { reactive } from 'vue'

// Global task-detail drawer, so any task (e.g. a command-palette search
// result) can be opened without the opening page needing its own local
// <TaskDrawer> instance. Existing pages (Board, Backlog, ...) keep their own
// local drawers for in-page task clicks — this one is additive, not a
// replacement, so it doesn't touch how those already work.
export const taskDrawerState = reactive({ taskId: null })

export function openTaskDrawer(taskId) { taskDrawerState.taskId = taskId }
export function closeTaskDrawer() { taskDrawerState.taskId = null }
