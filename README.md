<div align="center">

# ⚡ Pulse

### Agile delivery on ERPNext's own Projects and Tasks

A Plane / Jira / Linear-style delivery layer for the ERPNext you already run: sprints, a Kanban board, OKRs, risks and retrospectives on ERPNext Projects and Tasks, driven by AI through a built-in MCP server if you want.

`Frappe v16` · `ERPNext v16` · `Vue 3` · `frappe-ui` · `Python` · `MIT`

</div>

---

## Table of contents

- [What is Pulse](#what-is-pulse)
- [Why Pulse](#why-pulse)
- [Features](#features)
- [Screens](#screens)
- [Architecture](#architecture)
- [Installation](#installation)
- [First run](#first-run)
- [Roles & permissions](#roles--permissions)
- [AI control (MCP)](#ai-control-mcp)
- [Demo data](#demo-data)
- [Development](#development)
- [Data model](#data-model)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## What is Pulse

**Pulse** is an agile delivery layer for [ERPNext](https://erpnext.com) Projects and Tasks, built on the [Frappe framework](https://frappeframework.com). It gives delivery teams a fast, modern experience — projects, tasks with human-readable keys (`OPS-9`), a drag-and-drop board, sprints, backlog, per-user customizable dashboards, analytics, OKRs, risks, meetings, retrospectives, timesheets and a timestamped audit log — all delivered through a **Vue 3 single-page app** at `/pulse`, dark-themed by default.

Your projects and tasks stay **ERPNext Projects and Tasks**. Pulse adds a few fields to them (sprint, epic, board state, rank, release, issue key) and keeps its own records (sprints, OKRs, risks, meetings, retrospectives, timesheets, dashboards) linked to them, so ERPNext's reports, permissions and accounting links keep working.

## Why Pulse

Teams that already run ERPNext often plan their work in another tool and copy it back. Pulse keeps the plan where the projects already live:

- **On ERPNext's own records** — a card on the board is an ERPNext Task, so there is no second task list to sync.
- **Adds only what ERPNext lacks** — sprints, OKRs, risks, retrospectives and the rest are `Pulse *` doctypes linked to ERPNext Project and Task.
- **Modern UX** — a real SPA, not Desk forms: drag-drop board, command-style flows, restraint-first dark design.
- **AI-native** — ships an MCP server so assistants like Claude can create, edit, move and assign work in plain language.

## Features

### Projects & tasks
- Projects with a short **project key** (`OPS`, `PLM`) used to build task ids.
- **Human-readable task keys** — per-project running sequence (`OPS-9`, `PLS1-8`), auto-assigned on create and backfilled for existing tasks.
- Task types (Epic, Story, Bug, Feature, Improvement, Incident, Task, Sub-task) as ERPNext **Task Type** records, created on install.
- Priority, story points, due dates, description, labels.

### Board & work views
- **Drag-and-drop board** across Backlog → To Do → In Progress → In Review → Done, with optimistic updates.
- **Board / List** view toggle.
- **Filter & search** by type, priority, assignee, and free text.
- **Inline quick-add** per column and a full **New task** dialog.
- Rich **task drawer**: edit fields, assign people, checklist, comments, **sub-tasks** (with progress), and **dependencies** ("blocked by").

### Sprints & backlog
- Create and run sprints (planned / active / completed) with dates and goals.
- Backlog view ordered by rank.

### Dashboards & analytics
- **Per-user customizable dashboards** — add / move / resize widgets (KPI cards, charts, lists); layouts persist per user; admins can set a default template.
- **Analytics** view (MindPro-style): status distribution, tasks per assignee, type distribution, a story-point completion gauge, and sprint-progress bars.

### Delivery & governance
- **OKRs** (objectives, key results, check-ins, goals).
- **Risks** with actions and linked tasks.
- **Portfolios** grouping projects.
- **Meetings** (attendees, decisions, action items), **Retrospectives**, **Documents**, **Timesheets**.

### Assignment & audit
- **Create-and-assign in one step** — pick assignees while creating a task.
- **Hierarchical assignment**, enforced server-side: a user can only assign work at or below their own role rank (juniors can't assign upward).
- **Audit log** — a timestamped, unified activity feed (creates, status changes, assignments, comments) available as its own menu.

### AI control
- A bundled **MCP server** exposes 16 tools (list / create / update / move / assign / comment / sub-task / dependency / sprint / project …) so Claude Desktop or Claude Code can operate Pulse conversationally. See [`mcp/README.md`](mcp/README.md).

## Screens

> Add screenshots/GIFs here (Home, Board, Task drawer, Dashboard, Analytics, Audit log).

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Vue 3 SPA  (frappe-ui)         served at  /pulse          │
│  Board · Backlog · Sprints · Dashboards · Analytics · …    │
└───────────────▲──────────────────────────────────────────┘
                │  thin whitelisted REST  (pulse.api.*)
┌───────────────┴──────────────────────────────────────────┐
│  Pulse app  (Frappe / Python)                             │
│  ~50 Pulse doctypes · doc-events · permission hooks ·     │
│  hierarchical assignment · reports · schedulers           │
└───────────────▲──────────────────────────────────────────┘
                │  framework primitives + ERPNext Project / Task
┌───────────────┴──────────────────────────────────────────┐
│  Frappe framework  (auth · permissions · workflow · REST) │
└──────────────────────────────────────────────────────────┘
        (+ ERPNext v16: Project and Task are the records Pulse plans on)
```

- **Backend:** all logic in the `pulse` app; the public API lives under the `pulse.api.*` namespace and writes go through the standard document API so permissions and validations always fire.
- **Frontend:** a Vue 3 + frappe-ui app in [`frontend/`](frontend), built to `pulse/public/frontend` and served by a small website route at `/pulse`.
- **Depends on ERPNext:** `required_apps = ["erpnext"]`. Custom fields on ERPNext Project and Task are set up by `pulse/erpnext_bridge.py`; Pulse doctypes link only to ERPNext Project and Task, framework doctypes and other `Pulse *` doctypes.

## Installation

Prerequisites: a working [Frappe bench](https://frappeframework.com/docs/user/en/installation) with **Frappe v16 and ERPNext v16** installed on the site.

```bash
# from your bench directory
bench get-app https://github.com/mithtech-is/Pulse.git
bench --site your-site install-app pulse
```

### Build the frontend (only needed for a fresh git clone)

The repo ships pre-built assets, but if you're building from source:

```bash
cd apps/pulse/frontend
yarn install
yarn build
```

That's it — no extra services.

## First run

- Open **`/pulse`** on your site (e.g. `http://your-site:8000/pulse`), or click the **Pulse** tile in the Frappe **apps launcher** — Pulse also adds a **Pulse** entry to the Desk sidebar.
- Pulse users land in the app automatically after login.
- Create a **Project** (give it a key like `OPS`), then start adding tasks — task ids like `OPS-1` are generated for you.

## Roles & permissions

Pulse ships these roles, ranked for the assignment hierarchy (higher = more senior):

| Role | Rank |
|---|---|
| Pulse Admin | 100 |
| Pulse Manager | 80 |
| Pulse Team Lead | 60 |
| Pulse Senior Developer | 40 |
| Pulse Junior Developer | 20 |
| Pulse Intern | 10 |
| Pulse Viewer | 0 |

A user may assign work only to people **at or below** their own rank. This is enforced on the server, not just hidden in the UI. Ranks are configurable in **Pulse Settings**.

## AI control (MCP)

Pulse includes an MCP server so you can manage work by talking to Claude:

> *"Create a task in Operations: 'Prepare Q3 deck', high priority, assign bob@example.com, put it in To Do."*
> *"Move OPS-9 to In Progress and comment 'started'."*
> *"Add a sub-task 'write tests' under OPS-9."*

Setup (generate an API key, add to Claude Desktop / Code) is documented in **[`mcp/README.md`](mcp/README.md)**. The server exposes: `list_projects`, `list_tasks`, `get_task`, `list_sprints`, `list_users`, `create_task`, `update_task`, `move_task`, `assign_task`, `unassign_task`, `add_comment`, `add_subtask`, `add_dependency`, `delete_task`, `create_sprint`, `create_project`. All writes still pass Pulse's permission and hierarchy checks.

## Demo data

Populate every field of every doctype with realistic sample data (6 demo users, projects, tasks across all states, sprints, OKRs, risks, meetings, …):

```bash
bench --site your-site execute pulse.pulse.demo.showcase.run
# to remove it again:
bench --site your-site execute pulse.pulse.demo.showcase.clear
```

## Development

```bash
# backend: standard bench workflow
bench --site your-site migrate
bench start

# frontend: hot-reload dev server (proxies API to your bench)
cd apps/pulse/frontend
yarn install
yarn dev          # http://localhost:8080/pulse
yarn build        # production build into pulse/public/frontend
```

Project layout:

```
pulse/
├── frontend/                 # Vue 3 + frappe-ui SPA
│   └── src/{pages,components,ui,charts}
├── mcp/                      # MCP server for AI control
├── docs/                     # design docs (_canonical-model.md is the source of truth)
├── scripts/dev/              # throwaway dev/seed scripts
└── pulse/                    # the Frappe app
    ├── api/                  # pulse.api.*  (spa, dashboards, analytics, audit)
    ├── pulse/
    │   ├── doctype/          # ~50 Pulse doctypes
    │   ├── report/           # velocity, burndown, cumulative flow, …
    │   ├── demo/             # showcase seeder
    │   └── www/pulse.html    # serves the SPA at /pulse
    ├── hooks/                # doc-events, permissions, boot
    └── install.py            # roles, issue types, workflow, launcher, backfills
```

## Data model

Projects and tasks are ERPNext `Project` and `Task`, with Pulse's custom fields (see `pulse/erpnext_bridge.py`). Pulse adds 40 doctypes, all prefixed `Pulse `, including: `Pulse Sprint`, `Pulse Goal`, `Pulse Objective` / `Pulse Key Result` / `Pulse OKR Check-in`, `Pulse Risk` (+ actions), `Pulse Change Request`, `Pulse Meeting`, `Pulse Decision`, `Pulse Retrospective`, `Pulse Timesheet`, `Pulse Task Status Log`, `Pulse Dependency`, `Pulse Checklist`, `Pulse Comment`, `Pulse Dashboard` / `Pulse Dashboard Widget`, `Pulse Portfolio`, `Pulse Document`, `Pulse Recurring Task`, `Pulse Settings`, and their child tables.

## Roadmap

- Gantt / timeline view with dependency arrows
- Milestones surfaced on board and timeline
- Board swimlanes & WIP limits
- Command palette (⌘K) global search
- Real drag-resize dashboard grid
- Real-time board updates (websocket)

## FAQ

**Does it need ERPNext?** Yes, version 16. Pulse plans on ERPNext's own Projects and Tasks.

**Where does the UI live?** A Vue SPA at `/pulse`. The old Desk pages have been retired — the SPA is the only UI.

**Are my tasks the same as ERPNext Tasks?** Yes. A card on the board is an ERPNext Task; Pulse adds sprint, epic, board state and rank as fields on it.

**Can I use it without the frontend build step?** Yes — pre-built assets are committed. The build step is only for developing the UI.

## Contributing

Issues and PRs welcome. Keep Pulse's links to ERPNext limited to Project and Task, and add no dependency on other apps.

## Made by MithTech

Pulse is built and maintained by [MithTech](https://mith.tech), Frappe specialists in Bengaluru. We implement and support ERPNext and use Pulse on our own delivery.

- Product page: [mith.tech/products/pulse](https://mith.tech/products/pulse)
- Want it installed and run for you, or need ERPNext itself? [ERPNext implementation](https://mith.tech/services/erpnext-implementation) · [Talk to us](https://mith.tech/contact)

## License

[MIT](LICENSE)
