<template>
  <transition name="fade">
    <div v-if="paletteState.open" class="ovl" @click.self="close">
      <div class="panel" role="dialog" aria-modal="true" aria-label="Command palette">
        <div class="search-row">
          <SearchIcon class="w-4 h-4 text-faint shrink-0" />
          <input
            ref="inputEl"
            v-model="query"
            placeholder="Search tasks, projects, or jump to a page…"
            class="search-in"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="activate(activeIndex)"
            @keydown.esc="close"
          />
          <span class="kbd">Esc</span>
        </div>

        <div class="results" ref="listEl">
          <template v-if="query.trim()">
            <div v-if="matchedCommands.length" class="group">
              <div class="group-lbl">Go to</div>
              <button
                v-for="(item, i) in matchedCommands"
                :key="'cmd-' + item.to"
                :class="['row', { active: flatIndex(item) === activeIndex }]"
                @mouseenter="activeIndex = flatIndex(item)"
                @click="activate(flatIndex(item))"
              >
                <component :is="item.icon" class="w-[15px] h-[15px] text-faint shrink-0" />
                <span class="truncate">{{ item.label }}</span>
                <span class="row-hint">{{ item.section }}</span>
              </button>
            </div>

            <div v-if="matchedProjects.length" class="group">
              <div class="group-lbl">Projects</div>
              <button
                v-for="item in matchedProjects"
                :key="'proj-' + item.name"
                :class="['row', { active: flatIndex(item) === activeIndex }]"
                @mouseenter="activeIndex = flatIndex(item)"
                @click="activate(flatIndex(item))"
              >
                <span class="proj-key">{{ (item.pulse_project_key || '·').slice(0, 3) }}</span>
                <span class="truncate">{{ item.project_name || item.name }}</span>
              </button>
            </div>

            <div v-if="taskResults.length" class="group">
              <div class="group-lbl">Tasks</div>
              <button
                v-for="item in taskResults"
                :key="'task-' + item.name"
                :class="['row', { active: flatIndex(item) === activeIndex }]"
                @mouseenter="activeIndex = flatIndex(item)"
                @click="activate(flatIndex(item))"
              >
                <span class="task-key mono">{{ item.issue_key }}</span>
                <span class="truncate">{{ item.subject }}</span>
              </button>
            </div>

            <div v-if="searching" class="empty">Searching…</div>
            <div v-else-if="!matchedCommands.length && !matchedProjects.length && !taskResults.length" class="empty">
              No matches for "{{ query }}"
            </div>
          </template>

          <template v-else>
            <div class="group">
              <div class="group-lbl">Go to</div>
              <button
                v-for="item in navCommands"
                :key="'cmd-' + item.to"
                :class="['row', { active: flatIndex(item) === activeIndex }]"
                @mouseenter="activeIndex = flatIndex(item)"
                @click="activate(flatIndex(item))"
              >
                <component :is="item.icon" class="w-[15px] h-[15px] text-faint shrink-0" />
                <span class="truncate">{{ item.label }}</span>
                <span class="row-hint">{{ item.section }}</span>
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { call } from 'frappe-ui'
import { navCommands } from '../nav'
import { paletteState, closePalette } from '../ui/commandPalette'
import { openTaskDrawer } from '../ui/taskDrawer'
import SearchIcon from '~icons/lucide/search'

const router = useRouter()
const query = ref('')
const activeIndex = ref(0)
const inputEl = ref(null)
const listEl = ref(null)

const allProjects = ref([])
const taskResults = ref([])
const searching = ref(false)
let searchTimer = null
let searchSeq = 0

const matchedCommands = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return navCommands.filter((c) => c.label.toLowerCase().includes(q))
})

const matchedProjects = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return allProjects.value.filter((p) =>
    (p.project_name || p.name || '').toLowerCase().includes(q) ||
    (p.pulse_project_key || '').toLowerCase().includes(q),
  )
})

// Every visible row, in display order, so arrow keys and hover share one index.
const flatList = computed(() => {
  if (query.value.trim()) {
    return [...matchedCommands.value, ...matchedProjects.value, ...taskResults.value]
  }
  return [...navCommands]
})

function flatIndex(item) {
  return flatList.value.indexOf(item)
}

function move(delta) {
  if (!flatList.value.length) return
  activeIndex.value = (activeIndex.value + delta + flatList.value.length) % flatList.value.length
  nextTick(() => {
    listEl.value?.querySelector('.row.active')?.scrollIntoView({ block: 'nearest' })
  })
}

function activate(index) {
  const item = flatList.value[index]
  if (!item) return
  if (item.to) {
    router.push(item.to)
  } else if (item.issue_key) {
    openTaskDrawer(item.name)
  } else if ('project_name' in item || 'pulse_project_key' in item) {
    router.push(`/board?project=${encodeURIComponent(item.name)}`)
  }
  close()
}

function close() {
  closePalette()
  query.value = ''
  taskResults.value = []
  activeIndex.value = 0
}

// Debounced server search for tasks - subject/issue_key, same endpoint the
// dependency and subtask pickers already use elsewhere in the app.
watch(query, (q) => {
  activeIndex.value = 0
  clearTimeout(searchTimer)
  const trimmed = q.trim()
  if (trimmed.length < 2) {
    taskResults.value = []
    searching.value = false
    return
  }
  searching.value = true
  const seq = ++searchSeq
  searchTimer = setTimeout(async () => {
    const rows = await call('pulse.api.spa.search_tasks', { q: trimmed, limit: 8 }).catch(() => [])
    if (seq === searchSeq) {
      taskResults.value = rows || []
      searching.value = false
    }
  }, 250)
})

watch(() => paletteState.open, async (open) => {
  if (open) {
    if (!allProjects.value.length) {
      allProjects.value = await call('frappe.client.get_list', {
        doctype: 'Project', fields: ['name', 'project_name', 'pulse_project_key'], limit_page_length: 0,
      }).catch(() => [])
    }
    await nextTick()
    inputEl.value?.focus()
  }
})
</script>

<style scoped>
.ovl { position: fixed; inset: 0; z-index: 100; background: rgba(0, 0, 0, 0.5); display: grid; place-items: start center; padding-top: 12vh; }
.panel { width: 560px; max-width: calc(100vw - 32px); max-height: 60vh; display: flex; flex-direction: column; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow); overflow: hidden; }
.search-row { display: flex; align-items: center; gap: 9px; padding: 13px 15px; border-bottom: 1px solid var(--border-soft); }
.search-in { flex: 1; background: transparent; border: none; outline: none; color: var(--text); font-size: 14px; }
.search-in::placeholder { color: var(--faint); }
.results { overflow-y: auto; padding: 6px; }
.group + .group { margin-top: 4px; }
.group-lbl { padding: 6px 10px 4px; font-size: 10px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; color: var(--faint); }
.row { width: 100%; display: flex; align-items: center; gap: 9px; padding: 8px 10px; border-radius: 7px; text-align: left; color: var(--text); font-size: 13px; background: transparent; }
.row.active { background: var(--surface-2); }
.row-hint { margin-left: auto; font-size: 11px; color: var(--faint); shrink: 0; }
.proj-key, .task-key { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; padding: 1px 6px; border-radius: 5px; background: var(--surface-2); color: var(--accent); font-size: 10px; font-weight: 700; shrink: 0; }
.empty { padding: 20px 10px; text-align: center; color: var(--faint); font-size: 13px; }
.kbd { font-size: 10px; padding: 1px 5px; border-radius: 4px; background: var(--surface-2); border: 1px solid var(--border); color: var(--faint); }
</style>
