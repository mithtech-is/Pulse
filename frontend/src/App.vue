<template>
  <div class="flex h-full bg-app text-app text-sm">
    <!-- Sidebar -->
    <aside class="flex flex-col w-[232px] shrink-0 border-r border-app bg-surface">
      <div class="flex items-center gap-2.5 px-4 h-14 border-b border-app">
        <div class="w-[30px] h-[30px] rounded-xl grid place-items-center font-bold text-[15px]" style="background:var(--accent);color:var(--on-accent)">P</div>
        <div class="flex flex-col leading-none">
          <span class="text-[16px] font-bold tracking-tight">Pulse</span>
          <span class="text-[10px] text-faint mt-[3px]">Project management</span>
        </div>
      </div>

      <div class="px-2.5 pt-3 space-y-2">
        <button @click="openCreate()" class="new-btn w-full flex items-center justify-center gap-2 py-2.5 text-[13px] font-semibold">
          <Plus class="w-4 h-4" /> New task
        </button>
        <button @click="openPalette()" class="search-btn w-full flex items-center gap-2 px-2.5 py-2 text-[13px]">
          <Search class="w-[15px] h-[15px] text-faint" />
          <span class="text-faint">Search…</span>
          <span class="ml-auto kbd">{{ isMac ? '⌘K' : 'Ctrl K' }}</span>
        </button>
      </div>

      <nav class="flex-1 px-2 py-3 space-y-5 overflow-y-auto">
        <div v-for="group in nav" :key="group.section">
          <div class="px-2.5 pb-1.5 tele text-[10px] font-semibold text-faint flex items-center gap-1.5">{{ group.section }}</div>
          <template v-for="item in group.items" :key="item.to || item.href">
            <a v-if="item.href" :href="item.href" target="_blank"
              class="nav-item flex items-center gap-2.5 px-2.5 py-[7px] rounded-md text-[13px] hover-app">
              <component :is="item.icon" class="w-[15px] h-[15px] shrink-0" />
              <span>{{ item.label }}</span>
            </a>
            <router-link v-else :to="item.to"
              class="nav-item flex items-center gap-2.5 px-2.5 py-[7px] rounded-md text-[13px] hover-app"
              active-class="active">
              <component :is="item.icon" class="w-[15px] h-[15px] shrink-0" />
              <span>{{ item.label }}</span>
            </router-link>
          </template>
        </div>

        <div>
          <div class="px-2.5 pb-1.5 tele text-[10px] font-semibold text-faint flex items-center gap-1.5">Projects</div>
          <router-link v-for="p in projects" :key="p.name" :to="`/board?project=${encodeURIComponent(p.name)}`"
            class="nav-item flex items-center gap-2.5 px-2.5 py-[7px] rounded-md text-[13px] hover-app">
            <span class="w-[18px] h-[18px] grid place-items-center rounded-[5px] mono text-[8.5px] font-bold shrink-0"
              :style="{ background: 'var(--surface-2)', color: 'var(--accent)' }">{{ (p.pulse_project_key || '·').slice(0, 3) }}</span>
            <span class="truncate">{{ p.project_name || p.name }}</span>
          </router-link>
        </div>
      </nav>
      <div class="px-3 py-2.5 border-t border-soft flex items-center justify-between">
        <span class="flex items-center gap-2 min-w-0">
          <Avatar :name="user" :size="22" />
          <span class="text-[12px] text-muted truncate mono">{{ shortUser }}</span>
        </span>
        <button @click="onToggle" class="p-1.5 rounded-md hover-app text-muted" :title="theme === 'dark' ? 'Light mode' : 'Dark mode'">
          <Moon v-if="theme === 'dark'" class="w-[15px] h-[15px]" />
          <Sun v-else class="w-[15px] h-[15px]" />
        </button>
      </div>
    </aside>

    <main class="flex-1 overflow-auto min-w-0">
      <router-view />
    </main>

    <CreateIssueModal />
    <EntityForm />
    <CommandPalette />
    <TaskDrawer :task-id="taskDrawerState.taskId" @close="closeTaskDrawer" @changed="() => {}" @open="openTaskDrawer" />
    <Toaster />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { call } from 'frappe-ui'
import { theme, toggleTheme } from './theme'
import { openCreate } from './ui/create'
import { openPalette } from './ui/commandPalette'
import { taskDrawerState, closeTaskDrawer, openTaskDrawer } from './ui/taskDrawer'
import { nav } from './nav'
import Avatar from './ui/Avatar.vue'
import Toaster from './ui/Toaster.vue'
import CreateIssueModal from './components/CreateIssueModal.vue'
import EntityForm from './components/EntityForm.vue'
import CommandPalette from './components/CommandPalette.vue'
import TaskDrawer from './components/TaskDrawer.vue'
import Plus from '~icons/lucide/plus'
import Search from '~icons/lucide/search'
import Sun from '~icons/lucide/sun'
import Moon from '~icons/lucide/moon'

const user = ref('')
const projects = ref([])
const shortUser = computed(() => (user.value || '').split('@')[0])
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPod|iPad/.test(navigator.platform || navigator.userAgent || '')

function onToggle() { toggleTheme() }

// Cmd+K / Ctrl+K opens the command palette from anywhere in the app, matching
// the convention set by every tool this is meant to feel as fast as.
function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    openPalette()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', onKeydown)
  try { user.value = await call('frappe.auth.get_logged_user') } catch (e) { user.value = '' }
  projects.value = await call('frappe.client.get_list', {
    doctype: 'Project', fields: ['name', 'project_name', 'pulse_project_key'], limit_page_length: 0,
  }).catch(() => [])
})
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.nav-item { color: var(--muted); transition: color 0.12s, background 0.12s; }
.nav-item:hover { color: var(--text); }
.nav-item.active { color: var(--text); background: var(--surface-2); font-weight: 500; }
.nav-item.active :deep(svg) { color: var(--accent); }
.new-btn { background: var(--accent); transition: filter 0.12s; }
.new-btn:hover { filter: brightness(1.08); }
.search-btn { border: 1px solid var(--border); border-radius: 8px; color: var(--muted); transition: border-color 0.12s, background 0.12s; }
.search-btn:hover { border-color: var(--accent); background: var(--surface-2); }
.kbd { font-size: 10px; padding: 1px 5px; border-radius: 4px; background: var(--surface-2); border: 1px solid var(--border); color: var(--faint); }
</style>
