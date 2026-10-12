"""Pulse SPA endpoints (canonical namespace: pulse.api.spa.*).

Thin whitelisted endpoints for the Vue app: board, task detail, state changes,
assignment, comments, checklist. Writes go through the document API so
permissions + the hierarchical-assignment hook fire normally.
"""

import json

import frappe
from frappe import _

BOARD_COLUMNS = ["Backlog", "To Do", "In Progress", "In Review", "Done"]

PULSE_ROLES = {
    "Pulse Admin", "Pulse Manager", "Pulse Team Lead", "Pulse Senior Developer",
    "Pulse Junior Developer", "Pulse Intern", "Pulse Viewer",
}


def check_app_permission():
    """Whether the current user may see Pulse in the /apps launcher."""
    if frappe.session.user == "Administrator":
        return True
    roles = set(frappe.get_roles())
    return bool(roles & PULSE_ROLES) or "System Manager" in roles


def land_on_pulse(login_manager=None):
    """After login, send Pulse users straight into the SPA."""
    try:
        if check_app_permission():
            frappe.local.response["home_page"] = "/pulse"
    except Exception:
        pass

STATE_TO_STATUS = {
    "Backlog": "Open",
    "To Do": "Open",
    "In Progress": "Working",
    "In Review": "Pending Review",
    "Done": "Completed",
    "Cancelled": "Cancelled",
}
STATUS_TO_STATE = {
    "Open": "To Do",
    "Working": "In Progress",
    "Overdue": "In Progress",
    "Pending Review": "In Review",
    "Completed": "Done",
    "Cancelled": "Cancelled",
}


# Core ERPNext doctypes editable through the SPA's generic form, each with a
# curated field set so the dialog stays clean (not all ~60 ERPNext fields).
CORE_EDITABLE = {
    "Project": ["project_name", "status", "priority",
                "expected_start_date", "expected_end_date", "notes"],
    "Task": ["subject", "status", "priority",
             "exp_start_date", "exp_end_date", "description"],
}


def _is_editable(doctype):
    return bool(doctype) and (doctype.startswith("Pulse ") or doctype in CORE_EDITABLE)


def _assignees(assign):
    try:
        return frappe.parse_json(assign or "[]")
    except Exception:
        return []


def _column_of(task):
    return task.get("workflow_state") or STATUS_TO_STATE.get(task.get("status"), "Backlog")


def _publish_board(project=None):
    """Notify open boards to refresh (real-time). Requires the socketio process.

    Emitted immediately (not after_commit): every caller already commits before
    publishing, so deferring would wait on a commit that never arrives.
    """
    try:
        from frappe.realtime import get_site_room
        frappe.publish_realtime("pulse:board", {"project": project},
                                room=get_site_room(), after_commit=False)
    except Exception:
        pass


@frappe.whitelist()
def get_board(project=None, sprint=None):
    """Return board columns with their task cards."""
    filters = {}
    if project:
        filters["project"] = project
    if sprint:
        filters["pulse_sprint"] = sprint

    tasks = frappe.get_all(
        "Task",
        filters=filters,
        fields=[
            "name", "issue_key", "subject", "status", "workflow_state", "priority",
            "type as task_type", "project", "pulse_sprint",
            "exp_end_date", "_assign",
        ],
        order_by="pulse_rank asc, modified desc",
        limit_page_length=0,
    )
    columns = {c: [] for c in BOARD_COLUMNS}
    for t in tasks:
        t["assignees"] = _assignees(t.pop("_assign", None))
        col = _column_of(t)
        columns.setdefault(col, []).append(t)
    return {
        "columns": [{"name": c, "tasks": columns.get(c, [])} for c in BOARD_COLUMNS],
        "total": len(tasks),
    }


@frappe.whitelist()
def create_task(project, subject, state="Backlog", task_type=None, priority="Medium",
                description=None, assignees=None, pulse_sprint=None,
                exp_end_date=None, parent_task=None):
    """Create a task and (optionally) assign people to it in one step.

    Assignment goes through the standard mechanism, so the hierarchical-assignment
    rule fires: a user can only assign down/across, never above their own rank.
    """
    if isinstance(assignees, str):
        assignees = json.loads(assignees or "[]")
    assignees = [a for a in (assignees or []) if a]

    doc = frappe.get_doc({
        "doctype": "Task",
        "project": project,
        "subject": subject,
        "description": description,
        "type": task_type,
        "priority": priority or "Medium",
        "pulse_sprint": pulse_sprint,
        "exp_end_date": exp_end_date or None,
        "parent_task": parent_task,
        "workflow_state": state,
        "status": STATE_TO_STATUS.get(state, "Open"),
    })
    doc.insert()

    # Belt and braces: the issue key normally comes from the before_insert hook,
    # but a stale hook cache silently leaves tasks unkeyed. Issue keys are the
    # task's identity, so guarantee one here rather than trust hook registration.
    if not doc.get("issue_key"):
        from pulse.hooks.doc_events.task import assign_issue_key
        assign_issue_key(doc)
        if doc.get("issue_key"):
            frappe.db.set_value("Task", doc.name,
                                {"issue_key": doc.issue_key, "seq": doc.seq},
                                update_modified=False)

    from frappe.desk.form.assign_to import add as assign_add
    from pulse.api.audit import log

    assigned, blocked = [], []
    for user in assignees:
        try:
            assign_add({"assign_to": [user], "doctype": "Task", "name": doc.name})
            assigned.append(user)
            log("Assignment Changed", "Task", doc.issue_key or doc.name,
                project, f"Assigned {user} on create")
        except Exception as e:
            blocked.append({"user": user, "reason": str(e)})

    log("Task Created", "Task", doc.issue_key or doc.name, project, subject[:140])
    frappe.db.commit()
    _publish_board(project)
    return {
        "name": doc.name, "issue_key": doc.issue_key, "subject": doc.subject,
        "status": doc.status, "workflow_state": doc.workflow_state,
        "priority": doc.priority, "task_type": doc.get("type"),
        "project": doc.project,
        "assignees": assigned, "blocked": blocked,
    }


@frappe.whitelist()
def update_task_state(task, state):
    """Move a card to a new board column (updates workflow_state + status)."""
    if state not in STATE_TO_STATUS:
        frappe.throw(_("Unknown board column: {0}").format(state))
    doc = frappe.get_doc("Task", task)
    doc.workflow_state = state
    doc.status = STATE_TO_STATUS[state]
    doc.flags.ignore_links = True  # a stale epic/dep link shouldn't block a board move
    doc.save()
    from pulse.api.audit import log
    log("Status Changed", "Task", doc.issue_key or doc.name, doc.project,
        f"Moved to {state}")
    frappe.db.commit()
    _publish_board(doc.project)
    return {"name": doc.name, "workflow_state": doc.workflow_state, "status": doc.status}


@frappe.whitelist()
def get_task(task):
    """Full task detail for the drawer: fields, assignees, checklist, comments."""
    doc = frappe.get_doc("Task", task)
    checklist = frappe.get_all(
        "Pulse Checklist", filters={"task": task},
        fields=["name", "item", "is_done", "completed_by"],
        order_by="order_idx asc, creation asc",
    )
    comments = frappe.get_all(
        "Pulse Comment", filters={"task": task, "is_deleted": 0},
        fields=["name", "comment_text", "owner", "creation"],
        order_by="creation asc",
    )
    subtasks = frappe.get_all(
        "Task", filters={"parent_task": task},
        fields=["name", "issue_key", "subject", "status"], order_by="creation asc",
    )
    blocked_by = []
    for d in frappe.get_all("Pulse Dependency", filters={"source_task": task},
                            fields=["name", "target_task"]):
        info = frappe.db.get_value("Task", d.target_task,
                                   ["issue_key", "subject", "status"], as_dict=True) or {}
        blocked_by.append({"dep": d.name, "task": d.target_task, **info})

    parent = None
    if doc.get("parent_task"):
        parent = frappe.db.get_value("Task", doc.parent_task, ["issue_key", "subject"], as_dict=True)
        if parent:
            parent["name"] = doc.parent_task

    return {
        "name": doc.name, "issue_key": doc.issue_key,
        "subject": doc.subject, "description": doc.description,
        "status": doc.status, "workflow_state": doc.workflow_state,
        "priority": doc.priority, "task_type": doc.get("type"), "project": doc.project,
        "pulse_sprint": doc.pulse_sprint,
        "pulse_epic": doc.get("pulse_epic"), "pulse_release": doc.get("pulse_release"),
        "exp_start_date": doc.exp_start_date, "exp_end_date": doc.exp_end_date,
        "assignees": _assignees(doc.get("_assign")),
        "checklist": checklist, "comments": comments,
        "subtasks": subtasks, "blocked_by": blocked_by, "parent": parent,
    }


@frappe.whitelist()
def add_subtask(parent, subject):
    project = frappe.db.get_value("Task", parent, "project")
    # ERPNext only allows child tasks under a "group" task — promote the parent.
    if not frappe.db.get_value("Task", parent, "is_group"):
        frappe.db.set_value("Task", parent, "is_group", 1)
    child = create_task(project, subject, state="To Do", parent_task=parent)
    return {"name": child["name"], "issue_key": child["issue_key"],
            "subject": child["subject"], "status": child["status"]}


@frappe.whitelist()
def search_tasks(q=None, project=None, exclude=None, limit=10):
    filters = {}
    if project:
        filters["project"] = project
    if exclude:
        filters["name"] = ["!=", exclude]
    or_filters = None
    if q:
        or_filters = [["subject", "like", f"%{q}%"], ["issue_key", "like", f"%{q}%"]]
    rows = frappe.get_all("Task", filters=filters, or_filters=or_filters,
                          fields=["name", "issue_key", "subject"],
                          limit_page_length=int(limit), order_by="modified desc")
    return rows


@frappe.whitelist()
def add_dependency(task, depends_on):
    """`task` is blocked by `depends_on` (both are task names)."""
    if task == depends_on:
        frappe.throw(_("A task cannot depend on itself."))
    if frappe.db.exists("Pulse Dependency", {"source_task": task, "target_task": depends_on}):
        return {"ok": True}
    doc = frappe.get_doc({
        "doctype": "Pulse Dependency",
        "source_task": task, "target_task": depends_on,
        "source_project": frappe.db.get_value("Task", task, "project"),
        "target_project": frappe.db.get_value("Task", depends_on, "project"),
    })
    doc.insert()
    from pulse.api.audit import log
    key = frappe.db.get_value("Task", task, "issue_key") or task
    dep_key = frappe.db.get_value("Task", depends_on, "issue_key") or depends_on
    log("Dependency Added", "Task", key, doc.source_project, f"Blocked by {dep_key}")
    frappe.db.commit()
    return {"ok": True, "name": doc.name}


@frappe.whitelist()
def remove_dependency(name):
    frappe.delete_doc("Pulse Dependency", name, ignore_permissions=True)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def update_task(task, **fields):
    """Patch simple task fields from the detail drawer."""
    allowed = {
        "subject", "description", "priority", "task_type",
        "exp_start_date", "exp_end_date", "project",
        "pulse_sprint", "pulse_epic", "pulse_release",
    }
    doc = frappe.get_doc("Task", task)
    for k, v in fields.items():
        if k in allowed:
            doc.set("type" if k == "task_type" else k, v)
    doc.save()
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def assign_task(task, user):
    """Assign a user to a task (hierarchy hook enforces who may assign whom)."""
    from frappe.desk.form.assign_to import add
    add({"assign_to": [user], "doctype": "Task", "name": task})
    from pulse.api.audit import log
    key = frappe.db.get_value("Task", task, "issue_key") or task
    log("Assignment Changed", "Task", key,
        frappe.db.get_value("Task", task, "project"), f"Assigned {user}")
    frappe.db.commit()
    return {"assignees": _assignees(frappe.db.get_value("Task", task, "_assign"))}


@frappe.whitelist()
def unassign_task(task, user):
    from frappe.desk.form.assign_to import remove
    remove("Task", task, user)
    frappe.db.commit()
    return {"assignees": _assignees(frappe.db.get_value("Task", task, "_assign"))}


@frappe.whitelist()
def add_comment(task, text):
    project = frappe.db.get_value("Task", task, "project")
    doc = frappe.get_doc({
        "doctype": "Pulse Comment", "task": task, "project": project,
        "comment_text": text,
    }).insert()
    from pulse.api.audit import log
    key = frappe.db.get_value("Task", task, "issue_key") or task
    log("Comment Added", "Task", key, project, text[:140])
    frappe.db.commit()
    return {"name": doc.name, "comment_text": doc.comment_text,
            "owner": doc.owner, "creation": str(doc.creation)}


@frappe.whitelist()
def add_checklist_item(task, item):
    doc = frappe.get_doc({
        "doctype": "Pulse Checklist", "task": task, "item": item, "is_done": 0,
    }).insert()
    frappe.db.commit()
    return {"name": doc.name, "item": doc.item, "is_done": 0}


@frappe.whitelist()
def toggle_checklist_item(name, is_done):
    is_done = 1 if str(is_done) in ("1", "true", "True") else 0
    frappe.db.set_value("Pulse Checklist", name, {
        "is_done": is_done,
        "completed_by": frappe.session.user if is_done else None,
    })
    frappe.db.commit()
    return {"name": name, "is_done": is_done}


EDIT_SKIP_TYPES = {
    "Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold",
    "Heading", "Image", "Table", "Table MultiSelect", "Attach", "Attach Image",
    "Geolocation", "Signature", "Barcode", "Read Only",
}
EDIT_SKIP_FIELDS = {"issue_key", "seq", "task_counter", "workflow_state"}


@frappe.whitelist()
def get_form_meta(doctype):
    """Editable field schema for a Pulse (or core Project/Task) doctype.

    Project and Task are ERPNext doctypes with dozens of fields, so we expose a
    curated subset for the SPA's create/edit dialog rather than the whole form.
    """
    if not _is_editable(doctype):
        frappe.throw(_("This form can't be edited here."))
    meta = frappe.get_meta(doctype)

    def _field_dict(f):
        return {
            "fieldname": f.fieldname, "label": f.label or f.fieldname,
            "fieldtype": f.fieldtype, "options": f.options, "reqd": int(f.reqd or 0),
            "default": f.default, "description": f.description,
        }

    curated = CORE_EDITABLE.get(doctype)
    fields = []
    if curated:
        by_name = {f.fieldname: f for f in meta.fields}
        for fn in curated:
            f = by_name.get(fn)
            if f:
                fields.append(_field_dict(f))
    else:
        for f in meta.fields:
            if f.fieldtype in EDIT_SKIP_TYPES or f.hidden or f.read_only:
                continue
            if f.fieldname in EDIT_SKIP_FIELDS:
                continue
            fields.append(_field_dict(f))
    return {"doctype": doctype, "title_field": meta.title_field, "fields": fields}


@frappe.whitelist()
def link_options(doctype, txt=None):
    """Options for a Link field: name + best-guess title."""
    if not doctype:
        return []
    meta = frappe.get_meta(doctype)
    title = meta.title_field if meta.title_field and meta.title_field != "name" else None
    fields = ["name"] + ([title] if title else [])
    filters = {}
    rows = frappe.get_all(doctype, fields=fields, limit_page_length=50,
                          filters=filters, order_by="modified desc")
    out = []
    for r in rows:
        label = (r.get(title) if title else None) or r["name"]
        if txt and txt.lower() not in str(label).lower():
            continue
        out.append({"value": r["name"], "label": label})
    return out


@frappe.whitelist()
def save_entity(doc):
    """Insert or update any Pulse doctype record (permissions apply)."""
    if isinstance(doc, str):
        doc = json.loads(doc)
    dt = doc.get("doctype", "")
    if not _is_editable(dt):
        frappe.throw(_("This record can't be edited here."))

    reserved = {"doctype", "name", "modified", "creation", "owner", "modified_by", "idx"}
    name = doc.get("name")
    if name and frappe.db.exists(dt, name):
        d = frappe.get_doc(dt, name)  # fresh load → no timestamp mismatch
        for k, v in doc.items():
            if k not in reserved:
                d.set(k, v)
        d.save()
    else:
        d = frappe.get_doc({k: v for k, v in doc.items() if k != "name"})
        # ERPNext Project requires a Company; the curated Pulse form doesn't expose
        # it, so fall back to the site default.
        if dt == "Project" and d.meta.has_field("company") and not d.get("company"):
            from pulse.erpnext_bridge import ensure_default_company
            company = ensure_default_company()
            if not company:
                frappe.throw(_("No Company is configured. Complete ERPNext setup "
                               "(create a Company) before adding projects."))
            d.company = company
        d.insert()
    frappe.db.commit()
    return {"name": d.name, "doctype": d.doctype}


@frappe.whitelist()
def delete_entity(doctype, name):
    if not _is_editable(doctype):
        frappe.throw(_("This record can't be deleted here."))
    frappe.delete_doc(doctype, name)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def get_entity(doctype, name):
    if not _is_editable(doctype):
        frappe.throw(_("This record can't be read here."))
    return frappe.get_doc(doctype, name).as_dict()


@frappe.whitelist()
def delete_task(task):
    """Delete a task and its linked Pulse records (status logs, comments, checklist, deps)."""
    for dt, field in [("Pulse Task Status Log", "task"),
                      ("Pulse Comment", "task"),
                      ("Pulse Checklist", "task")]:
        for n in frappe.get_all(dt, filters={field: task}, pluck="name"):
            frappe.delete_doc(dt, n, force=True, ignore_permissions=True)

    # Activity log rows point at the task by dynamic link, recorded either by
    # name or by issue key depending on the write path — clear both.
    refs = [task]
    issue_key = frappe.db.get_value("Task", task, "issue_key")
    if issue_key:
        refs.append(issue_key)
    frappe.db.delete("Pulse Activity Log",
                     {"reference_doctype": "Task", "reference_name": ["in", refs]})
    deps = (frappe.get_all("Pulse Dependency", filters={"source_task": task}, pluck="name")
            + frappe.get_all("Pulse Dependency", filters={"target_task": task}, pluck="name"))
    for d in deps:
        frappe.delete_doc("Pulse Dependency", d, force=True, ignore_permissions=True)
    for st in frappe.get_all("Task", filters={"parent_task": task}, pluck="name"):
        frappe.db.set_value("Task", st, "parent_task", None)
    # time entries are child rows (Pulse Timesheet Entry) linked to this task —
    # remove them directly so the link doesn't block deletion.
    frappe.db.delete("Pulse Timesheet Entry", {"task": task})
    frappe.delete_doc("Task", task)
    frappe.db.commit()
    _publish_board()
    return {"ok": True}


@frappe.whitelist()
def my_todos():
    """Personal to-do list: open tasks assigned to the current user, all projects.

    Ordered so dated work comes first (soonest due), undated last.
    """
    me = frappe.session.user
    return frappe.get_all(
        "Task",
        filters=[["_assign", "like", f"%{me}%"],
                 ["status", "not in", ["Completed", "Cancelled"]]],
        fields=["name", "issue_key", "subject", "status", "workflow_state", "priority",
                "type as task_type", "project", "exp_end_date"],
        order_by="exp_end_date asc, modified desc",
        limit_page_length=0,
    )


@frappe.whitelist()
def list_attachments(task):
    """Files attached to a task (upload is done via the core /api/method/upload_file)."""
    name = task if frappe.db.exists("Task", task) else resolve_task(task)
    return frappe.get_all(
        "File", filters={"attached_to_doctype": "Task", "attached_to_name": name},
        fields=["name", "file_name", "file_url", "is_private", "file_size"],
        order_by="creation desc",
    )


@frappe.whitelist()
def delete_attachment(name):
    frappe.delete_doc("File", name)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def resolve_task(ref):
    """Return the internal task name for a given issue key (e.g. PLS5-3) or name."""
    if frappe.db.exists("Task", ref):
        return ref
    name = frappe.db.get_value("Task", {"issue_key": ref}, "name")
    if not name:
        frappe.throw(_("No task found for '{0}'").format(ref))
    return name


@frappe.whitelist()
def get_assignable_users():
    """Users the current user may assign work to (respecting hierarchy)."""
    from pulse.services.hierarchy_service import can_assign
    me = frappe.session.user
    users = frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"],
        limit_page_length=0,
    )
    out = []
    for u in users:
        if u.name in ("Administrator", "Guest"):
            continue
        if "Pulse Admin" in frappe.get_roles(me) or can_assign(me, u.name):
            out.append(u)
    return out
