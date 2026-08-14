// Sidebar nav, extracted from App.vue so CommandPalette.vue can list the same
// destinations as "go to" commands without a second copy of this list to drift.
import House from '~icons/lucide/house'
import LayoutDashboard from '~icons/lucide/layout-dashboard'
import ChartColumn from '~icons/lucide/chart-column'
import FileBarChart from '~icons/lucide/file-bar-chart'
import SquareCheckBig from '~icons/lucide/square-check-big'
import ListChecks from '~icons/lucide/list-checks'
import SquareKanban from '~icons/lucide/square-kanban'
import List from '~icons/lucide/list'
import CalendarDays from '~icons/lucide/calendar-days'
import Repeat from '~icons/lucide/repeat'
import Folder from '~icons/lucide/folder'
import Layers from '~icons/lucide/layers'
import Zap from '~icons/lucide/zap'
import Tag from '~icons/lucide/tag'
import Target from '~icons/lucide/target'
import ShieldAlert from '~icons/lucide/shield-alert'
import Users from '~icons/lucide/users'
import RefreshCw from '~icons/lucide/refresh-cw'
import FileText from '~icons/lucide/file-text'
import Clock from '~icons/lucide/clock'
import ScrollText from '~icons/lucide/scroll-text'
import Settings from '~icons/lucide/settings'

export const nav = [
  { section: 'Work', items: [
    { to: '/', label: 'Home', icon: House },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/analytics', label: 'Analytics', icon: ChartColumn },
    { to: '/reports', label: 'Reports', icon: FileBarChart },
    { to: '/todo', label: 'To Do', icon: ListChecks },
    { to: '/my-work', label: 'My Work', icon: SquareCheckBig },
    { to: '/board', label: 'Board', icon: SquareKanban },
    { to: '/backlog', label: 'Backlog', icon: List },
    { to: '/sprints', label: 'Sprints', icon: CalendarDays },
    { to: '/recurring', label: 'Recurring', icon: Repeat },
    { to: '/projects', label: 'Projects', icon: Folder },
  ] },
  { section: 'Plan', items: [
    { to: '/epics', label: 'Epics', icon: Zap },
    { to: '/releases', label: 'Releases', icon: Tag },
    { to: '/m/portfolio', label: 'Portfolio', icon: Layers },
    { to: '/m/okrs', label: 'OKRs', icon: Target },
    { to: '/m/risks', label: 'Risks', icon: ShieldAlert },
  ] },
  { section: 'Collaborate', items: [
    { to: '/m/meetings', label: 'Meetings', icon: Users },
    { to: '/m/retros', label: 'Retrospectives', icon: RefreshCw },
    { to: '/m/documents', label: 'Documents', icon: FileText },
    { to: '/m/timesheets', label: 'Timesheets', icon: Clock },
  ] },
  { section: 'System', items: [
    { to: '/audit', label: 'Audit Logs', icon: ScrollText },
    { href: '/app/pulse-settings', label: 'Settings', icon: Settings },
  ] },
]

/** Flat list of navigable commands (href items excluded — those aren't router destinations). */
export const navCommands = nav.flatMap((group) =>
  group.items.filter((item) => item.to).map((item) => ({ ...item, section: group.section })),
)
