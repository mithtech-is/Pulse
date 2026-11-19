# Pulse: handoff

Updated 2026-11-19.

## What it is

Pulse is agile delivery on ERPNext's own Projects and Tasks: sprints, a Kanban board, OKRs, risks and retrospectives. It runs on Frappe v16 and ERPNext v16. The front end is Vue 3 with frappe-ui. It has a built-in MCP server. MIT licence. Publisher: MithTech.

## State

- Default branch `main`. Work on `wip`.
- Ship with `git ship`.
- Gate: no gate found (no `.claude/gate`, no npm gate script).
- Deploy: none named.
- Install on a bench: `bench get-app https://github.com/mithtech-is/Pulse.git`, then `bench --site <site> install-app pulse`, `bench --site <site> migrate`, `bench start`.
- Last notable work (git log, `main`):
  - `8c74ae0` merged README and maintainer links (2026-11-18).
  - `77889ec` Project filter fix in reports.
  - `e846b57` soft-card UI and overview dashboard.

## Open work

- No open work is recorded.

## Read next

- `README.md` (the full doc: doctypes, MCP, demo commands).
- `docs/_canonical-model.md`.
- `patches.txt`. Check it before any bench upgrade.
- `superproductivity-plugin/` is a separate plugin folder.
