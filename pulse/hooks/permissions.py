import frappe


def task_query_conditions(user=None):
    user = user or frappe.session.user
    if "Pulse Admin" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(
        user
    ):
        return ""
    conditions = []
    projects = _allowed_projects(user)
    if projects is not None:
        plist = ", ".join(frappe.db.escape(p) for p in projects)
        conditions.append(f"`tabTask`.`project` in ({plist})")
    top_role = _top_pulse_role(user)
    if top_role in ("Pulse Junior Developer", "Pulse Intern"):
        u = frappe.db.escape(user)
        conditions.append(
            f"(`tabTask`.`_assign` like {frappe.db.escape('%' + user + '%')} "
            f"or `tabTask`.`owner` = {u})"
        )
    return " and ".join(conditions)


def sprint_query_conditions(user=None):
    user = user or frappe.session.user
    if "Pulse Admin" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(
        user
    ):
        return ""
    projects = _allowed_projects(user)
    if projects is not None:
        plist = ", ".join(frappe.db.escape(p) for p in projects)
        return f"`tabPulse Sprint`.`project` in ({plist})"
    return ""


def status_log_query_conditions(user=None):
    user = user or frappe.session.user
    if "Pulse Admin" in frappe.get_roles(user) or "System Manager" in frappe.get_roles(
        user
    ):
        return ""
    projects = _allowed_projects(user)
    if projects is not None:
        plist = ", ".join(frappe.db.escape(p) for p in projects)
        return f"`tabPulse Task Status Log`.`project` in ({plist})"
    return ""


def _allowed_projects(user):
    cache_key = f"_allowed_projects:{user}"
    if hasattr(frappe.local, cache_key):
        return getattr(frappe.local, cache_key)
    # membership now lives on ERPNext Project.users (Project User child table)
    project_users = frappe.get_all(
        "Project User",
        filters={"user": user, "parenttype": "Project"},
        pluck="parent",
    )
    result = project_users if project_users else None
    setattr(frappe.local, cache_key, result)
    return result


def _top_pulse_role(user):
    cache_key = f"_top_pulse_role:{user}"
    if hasattr(frappe.local, cache_key):
        return getattr(frappe.local, cache_key)
    pulse_roles = [
        "Pulse Admin",
        "Pulse Manager",
        "Pulse Team Lead",
        "Pulse Senior Developer",
        "Pulse Junior Developer",
        "Pulse Intern",
        "Pulse Viewer",
    ]
    user_roles = frappe.get_roles(user)
    for role in pulse_roles:
        if role in user_roles:
            setattr(frappe.local, cache_key, role)
            return role
    setattr(frappe.local, cache_key, None)
    return None


def on_todo_assign(doc, method=None):
    from pulse.hooks.doc_events.assignment import enforce_hierarchy

    enforce_hierarchy(doc, method)


def validate_task_assignees(doc, method=None):
    if doc.flags.get("from_pulse"):
        return
    before = doc.get_doc_before_save()
    if before is None:
        return
    # `_assign` is only set on a document once someone is assigned; .get() reads None otherwise
    old_assign = frappe.parse_json(before.get("_assign") or "[]")
    new_assign = frappe.parse_json(doc.get("_assign") or "[]")
    added = [u for u in new_assign if u not in old_assign]
    for user in added:
        from pulse.hooks.doc_events.assignment import validate_assignment

        validate_assignment(frappe.session.user, user)
