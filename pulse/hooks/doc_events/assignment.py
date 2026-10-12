import frappe
from frappe import _

from pulse.services.hierarchy_service import can_assign, hierarchy_enabled


def enforce_hierarchy(doc, method=None):
    if getattr(doc, "doctype", None) != "ToDo":
        return
    # The hierarchy governs work in Pulse: Task assignments made by people.
    # ToDos on other doctypes (Lead, Opportunity, ...) and assignments made by
    # an Assignment Rule are the rest of ERPNext's business, not Pulse's.
    if doc.get("reference_type") != "Task" or doc.get("assignment_rule"):
        return
    assignee = doc.get("allocated_to")
    if not assignee:
        return
    if not hierarchy_enabled():
        return
    assigner = doc.get("assigned_by") or frappe.session.user
    if assigner in ("Administrator",):
        return
    if not can_assign(assigner, assignee):
        frappe.throw(
            _(
                "You can only assign work to people at or below your role level. "
                "{0} is ranked above you."
            ).format(frappe.bold(assignee)),
            title=_("Assignment not allowed"),
        )


def validate_assignment(assigner, assignee, doc=None):
    if not hierarchy_enabled():
        return
    if assigner in ("Administrator",) or "Pulse Admin" in frappe.get_roles(assigner):
        return
    if assigner == assignee:
        return
    if not can_assign(assigner, assignee):
        frappe.throw(
            _(
                "You cannot assign work to {0}: their role rank ({1}) is higher than yours ({2}). "
                "Assignment is allowed only down or across the hierarchy."
            ).format(
                assignee,
                _get_rank(assignee),
                _get_rank(assigner),
            ),
            title=_("Assignment Not Allowed"),
        )


def _get_rank(user):
    from pulse.services.hierarchy_service import get_user_max_rank

    return get_user_max_rank(user)
