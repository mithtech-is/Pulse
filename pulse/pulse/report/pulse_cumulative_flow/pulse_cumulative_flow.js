frappe.query_reports["Pulse Cumulative Flow"] = {
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
            "label": __("From Date"),
            "fieldtype": "Date"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date"
        }
    ]
};
