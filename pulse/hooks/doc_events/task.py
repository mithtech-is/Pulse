import re

import frappe
from frappe.utils import now_datetime, today


def before_insert(doc, method=None):
    assign_issue_key(doc)


def sync_status_from_board(doc, method=None):
    """A board column set in the Desk form moves Status too, as a drag on the board does.

    update_task_state (the board) writes both; the form only wrote Board State, so a
    task could show Done on the board and Pending Review in ERPNext.
    """
    from pulse.api.spa import STATE_TO_STATUS

    state = doc.get("workflow_state")
    before = doc.get_doc_before_save()
    if not state or (before is not None and before.get("workflow_state") == state):
        return
    status = STATE_TO_STATUS.get(state)
    if status and doc.status != status:
        doc.status = status
        if status == "Completed" and not doc.get("completed_on"):
            doc.completed_on = today()


def on_update(doc, method=None):
    # logging / rollups are side-effects — never let them block a Task save
    try:
        _log_status_change(doc)
    except Exception:
        frappe.log_error(title="Pulse: status log failed", message=frappe.get_traceback())
    try:
        _rollup_sprint_tasks(doc)
    except Exception:
        frappe.log_error(title="Pulse: sprint rollup failed", message=frappe.get_traceback())
    try:
        from pulse.api import notify
        notify.notify_task_completed(doc)
    except Exception:
        frappe.log_error(title="Pulse: completion notify failed", message=frappe.get_traceback())


# ---------------------------------------------------------------------------
# Human-readable issue keys (e.g. OPS-9)
# ---------------------------------------------------------------------------

def assign_issue_key(doc):
    if doc.get("issue_key") or not doc.get("project"):
        return
    key = ensure_project_key(doc.project)
    # Atomic per-project sequence. GREATEST(...) with the current max task seq makes
    # this self-heal: if the counter ever drifts behind existing keys (e.g. tasks were
    # deleted, which never rolls the counter back), we skip past them instead of
    # colliding on a duplicate issue_key.
    frappe.db.sql(
        """UPDATE `tabProject` p
           SET p.task_counter = GREATEST(
               COALESCE(p.task_counter, 0),
               COALESCE((SELECT MAX(t.seq) FROM `tabTask` t WHERE t.project = p.name), 0)
           ) + 1
           WHERE p.name = %s""",
        (doc.project,),
    )
    seq = frappe.db.sql(
        "SELECT task_counter FROM `tabProject` WHERE name = %s", (doc.project,)
    )[0][0]
    doc.seq = seq
    doc.issue_key = f"{key}-{seq}"


def ensure_project_key(project):
    key = frappe.db.get_value("Project", project, "pulse_project_key")
    if key:
        return key
    name = frappe.db.get_value("Project", project, "project_name") or project
    key = _make_key(name)
    # guarantee uniqueness across projects
    base, n = key, 1
    taken = set(
        frappe.get_all("Project", filters={"name": ["!=", project]},
                       pluck="pulse_project_key")
    )
    while key in taken:
        n += 1
        key = f"{base}{n}"
    frappe.db.set_value("Project", project, "pulse_project_key", key)
    return key


def _make_key(name):
    words = re.findall(r"[A-Za-z0-9]+", (name or "").upper())
    if not words:
        return "PRJ"
    if len(words) == 1:
        return words[0][:4]
    return "".join(w[0] for w in words)[:5]


def _log_status_change(doc):
    to_state = doc.get("workflow_state") or doc.status
    if not to_state:
        return
    
    status_map = {
        "Open": "To Do",
        "Working": "In Progress",
        "Pending Review": "In Review",
        "Completed": "Done",
        "Cancelled": "Cancelled"
    }
    if to_state in status_map:
        to_state = status_map[to_state]
        
    before = doc.get_doc_before_save()
    from_state = (before.get("workflow_state") or before.status) if before is not None else None
    if from_state in status_map:
        from_state = status_map[from_state]
        
    if before is not None and from_state == to_state:
        return
    log = frappe.new_doc("Pulse Task Status Log")
    log.task = doc.name
    log.project = doc.project if frappe.db.exists("Project", doc.project) else None
    log.sprint = doc.get("pulse_sprint")
    log.from_state = from_state
    log.to_state = to_state
    log.changed_by = frappe.session.user
    log.changed_on = now_datetime()
    log.flags.ignore_links = True
    log.insert(ignore_permissions=True)


def _rollup_sprint_tasks(doc):
    sprint = doc.get("pulse_sprint")
    if not sprint or not frappe.db.exists("Pulse Sprint", sprint):
        return
    before = doc.get_doc_before_save()
    old_sprint = before.get("pulse_sprint") if before else None
    old_status = before.get("status") if before else None
    # only recount when sprint membership or completion state actually changed
    if sprint == old_sprint and old_status == doc.get("status"):
        return
    try:
        frappe.get_doc("Pulse Sprint", sprint).recalculate_tasks()
    except Exception:
        frappe.log_error(
            title="Pulse: sprint task rollup failed",
            message=frappe.get_traceback(),
        )
    if (
        old_sprint
        and old_sprint != sprint
        and frappe.db.exists("Pulse Sprint", old_sprint)
    ):
        try:
            frappe.get_doc("Pulse Sprint", old_sprint).recalculate_tasks()
        except Exception:
            frappe.log_error(
                title="Pulse: sprint point rollup failed",
                message=frappe.get_traceback(),
            )
