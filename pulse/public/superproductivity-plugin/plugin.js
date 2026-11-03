/**
 * Pulse Sync — Super Productivity plugin.
 *
 * - Imports your assigned Pulse tasks into Super Productivity.
 * - Pushes tracked time back to Pulse (hours only, no billing).
 * - Marks the Pulse task Done when you complete it in Super Productivity.
 *
 * Config (Pulse URL + API key/secret) is entered in the plugin's side panel
 * (index.html) and stored via PluginAPI.persistDataSynced.
 */

const PULSE_REF = /pulse:(\S+)/; // stored in task.notes to link SP task <-> Pulse task

async function getConfig() {
  try {
    const raw = await PluginAPI.loadSyncedData();
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

async function pulse(cfg, method, params) {
  const base = (cfg.url || '').replace(/\/+$/, '');
  const headers = {
    'Authorization': 'token ' + cfg.apiKey + ':' + cfg.apiSecret,
    'Content-Type': 'application/json',
  };
  if (cfg.siteHost) headers['Host'] = cfg.siteHost;
  const res = await fetch(base + '/api/method/' + method, {
    method: 'POST',
    headers,
    body: JSON.stringify(params || {}),
  });
  if (!res.ok) throw new Error('Pulse HTTP ' + res.status);
  const data = await res.json();
  return data.message;
}

// ---- Import assigned Pulse tasks into Super Productivity ----
async function importFromPulse() {
  const cfg = await getConfig();
  if (!cfg.url) { PluginAPI.showSnack({ msg: 'Configure Pulse first (Pulse Sync panel).' }); return; }
  let tasks;
  try {
    tasks = await pulse(cfg, 'pulse.api.time.my_tasks', {});
  } catch (e) {
    PluginAPI.showSnack({ msg: 'Pulse import failed: ' + e.message });
    return;
  }
  const existing = await PluginAPI.getTasks();
  let added = 0;
  for (const t of tasks || []) {
    const ref = 'pulse:' + t.name;
    if (existing.some((x) => (x.notes || '').includes(ref))) continue;
    await PluginAPI.addTask({
      title: t.issue_key + ' — ' + t.subject,
      notes: ref,
    });
    added++;
  }
  PluginAPI.showSnack({ msg: 'Pulse: imported ' + added + ' new task(s).' });
}

// ---- Push tracked time back to Pulse ----
async function pushTimeToPulse() {
  const cfg = await getConfig();
  if (!cfg.url) return;
  const synced = cfg._synced || {}; // { pulseTaskName: hoursAlreadyPushed }
  const tasks = await PluginAPI.getTasks();
  let pushed = 0;
  for (const t of tasks) {
    const m = (t.notes || '').match(PULSE_REF);
    if (!m) continue;
    const pulseName = m[1];
    const spentH = Math.round(((t.timeSpent || 0) / 3600000) * 100) / 100; // ms -> hours
    const delta = Math.round((spentH - (synced[pulseName] || 0)) * 100) / 100;
    if (delta > 0.01) {
      try {
        await pulse(cfg, 'pulse.api.time.log_time', { task: pulseName, hours: delta });
        synced[pulseName] = spentH;
        pushed += delta;
      } catch (e) { /* keep going */ }
    }
  }
  cfg._synced = synced;
  await PluginAPI.persistDataSynced(JSON.stringify(cfg));
  if (pushed > 0) PluginAPI.showSnack({ msg: 'Pulse: pushed ' + pushed.toFixed(2) + ' h.' });
}

// expose actions to the config iframe (index.html) via window
window.pulseImport = importFromPulse;
window.pulsePushTime = pushTimeToPulse;

// ---- UI: side-panel button opens the config/actions view ----
if (PluginAPI.registerSidePanelButton) {
  PluginAPI.registerSidePanelButton({
    label: 'Pulse Sync',
    icon: 'sync',
    onClick: () => PluginAPI.showIndexHtmlAsView && PluginAPI.showIndexHtmlAsView(),
  });
}
if (PluginAPI.registerHeaderButton) {
  PluginAPI.registerHeaderButton({
    label: 'Import from Pulse',
    icon: 'cloud_download',
    onClick: importFromPulse,
  });
}

// ---- Hooks ----
if (PluginAPI.registerHook) {
  PluginAPI.registerHook('finishDay', pushTimeToPulse);
  PluginAPI.registerHook('taskComplete', async (task) => {
    const cfg = await getConfig();
    const m = (task && task.notes ? task.notes : '').match(PULSE_REF);
    if (cfg.url && m) {
      try { await pulse(cfg, 'pulse.api.spa.update_task_state', { task: m[1], state: 'Done' }); } catch (e) {}
    }
  });
}
