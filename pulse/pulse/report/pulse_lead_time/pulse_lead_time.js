frappe.query_reports["Pulse Lead Time"] = {
    "filters": [
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "reqd": 1
        },
        {
            "fieldname": "sprint",
            "label": __("Sprint"),
            "fieldtype": "Link",
            "options": "Pulse Sprint",
            "get_query": function() {
                let project = frappe.query_report.get_filter_value("project");
                return project ? {
                    filters: { project: project }
                } : {};
            }
        },
        {
            "fieldname": "from_date",
            "label": __("Done From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "to_date",
            "label": __("Done To Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "task_type",
            "label": __("Issue Type"),
            "fieldtype": "Link",
            "options": "Pulse Issue Type"
        },
        {
            "fieldname": "assignee",
            "label": __("Assignee"),
            "fieldtype": "Link",
            "options": "User"
        }
    ]
};
