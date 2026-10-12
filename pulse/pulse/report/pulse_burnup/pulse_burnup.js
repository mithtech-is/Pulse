frappe.query_reports["Pulse Burnup"] = {
    "filters": [
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project"
        },
        {
            "fieldname": "sprint",
            "label": __("Sprint"),
            "fieldtype": "Link",
            "options": "Pulse Sprint",
            "reqd": 1,
            "get_query": function() {
                let project = frappe.query_report.get_filter_value("project");
                return project ? {
                    filters: { project: project }
                } : {};
            }
        }
    ]
};
