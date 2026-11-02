from collections import Counter


def generate_dashboard_summary(tickets):
    """Generate statistics from saved CampusFlow tickets."""

    total_tickets = len(tickets)

    categories = Counter()
    priorities = Counter()
    departments = Counter()
    statuses = Counter()

    department_totals = Counter()
    department_resolved = Counter()

    classified_tickets = 0
    resolved_tickets = 0

    for ticket in tickets:

        category = ticket.get("category", "Unclassified")
        priority = ticket.get("priority", "Unassigned")
        department = ticket.get("department", "Unassigned")
        status = ticket.get("status", "Open")

        # Count ticket distributions
        categories[category] += 1
        priorities[priority] += 1
        departments[department] += 1
        statuses[status] += 1

        # Count AI-classified tickets
        if category != "Unclassified":
            classified_tickets += 1

        # Count department workload
        department_totals[department] += 1

        # Count resolved tickets
        if status == "Resolved":
            resolved_tickets += 1
            department_resolved[department] += 1

    # Calculate unclassified tickets
    unclassified_tickets = total_tickets - classified_tickets

    # Calculate outstanding tickets
    outstanding_tickets = total_tickets - resolved_tickets

    # Calculate overall resolution percentage
    resolution_rate = (
        (resolved_tickets / total_tickets) * 100
        if total_tickets > 0 else 0
    )

    # Calculate resolution performance for each department
    department_resolution = {}

    for department, department_total in department_totals.items():

        resolved = department_resolved[department]

        department_rate = (
            (resolved / department_total) * 100
            if department_total > 0 else 0
        )

        department_resolution[department] = {
            "total_tickets": department_total,
            "resolved_tickets": resolved,
            "resolution_rate": round(department_rate, 1)
        }

    return {
        "total_tickets": total_tickets,
        "classified_tickets": classified_tickets,
        "unclassified_tickets": unclassified_tickets,
        "categories": dict(categories),
        "priorities": dict(priorities),
        "departments": dict(departments),
        "statuses": dict(statuses),
        "resolved_tickets": resolved_tickets,
        "outstanding_tickets": outstanding_tickets,
        "resolution_rate": round(resolution_rate, 1),
        "department_resolution": department_resolution
    }