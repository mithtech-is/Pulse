# Pulse Sync — Super Productivity plugin

Track your Pulse work in [Super Productivity](https://super-productivity.com) and send the time back to Pulse.

- **Import** your assigned Pulse tasks into Super Productivity (as `PLS1-8 — Fix login`).
- **Track time** in Super Productivity as usual (start/stop timer).
- **Push time back** — logged hours flow to the Pulse task (hours only, no billing).
- **Complete** a task in Super Productivity → it's marked **Done** in Pulse.

## How it links
Each imported SP task stores `pulse:<task-id>` in its notes. That reference is how time and completion sync back to the right Pulse task — don't remove it.

## Install
1. In Super Productivity: **Settings → Plugins → Load Plugin from Folder** (enable plugins first if prompted).
2. Point it at this folder (`superproductivity-plugin/`) — it contains `manifest.json`, `plugin.js`, `index.html`, `icon.svg`.
3. Open the **Pulse Sync** side panel.

## Configure
In the Pulse Sync panel, fill in:
- **Pulse URL** — e.g. `http://172.23.107.104:8000`
- **Site host** — `project.local` (only if your site is served by hostname, e.g. WSL)
- **API key / secret** — generate in **Pulse → avatar → My Settings → API Access → Generate Keys**

Click **Save**, then **Import my tasks**. Track time, and **Push time** (or it auto-pushes on *Finish Day*).

## One server-side requirement: CORS
Because the plugin calls Pulse's REST API from Super Productivity's origin, enable CORS on the Frappe site. In `sites/<your-site>/site_config.json` (or `common_site_config.json`) add:

```json
{
  "allow_cors": "*"
}
```
For production, set the specific Super Productivity origin instead of `*`. Restart bench after changing it.

## Endpoints used
- `pulse.api.time.my_tasks` — your assigned tasks
- `pulse.api.time.log_time` — log hours on a task
- `pulse.api.spa.update_task_state` — mark Done on completion

## Notes
- Targets the Super Productivity **plugin API v9+**. If your version differs, the API method/hook names in `plugin.js` / `index.html` may need minor adjustment (`getTasks`, `addTask`, `persistDataSynced`, `registerHook`, `showIndexHtmlAsView`).
- Time is hours-only by design — no billable flag, no rates, no cost.
