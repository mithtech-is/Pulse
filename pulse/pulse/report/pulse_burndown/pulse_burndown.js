frappe.query_reports["Pulse Burndown"] = {
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
            "get_query": function() {
                let project = frappe.query_report.get_filter_value("project");
                return project ? {
                    filters: { project: project }
                } : {};
            }
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "actual_remaining" && data && data.actual_remaining < 0) {
            value = "<span style='color:red'>" + value + "</span>";
        }
        return value;
    }
};
