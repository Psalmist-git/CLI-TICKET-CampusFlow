from reports import generate_dashboard_summary


def test_dashboard_counts_tickets_correctly():
    tickets = [
        {
            "category": "Network",
            "priority": "High",
            "department": "ICT",
            "status": "Resolved"
        },
        {
            "category": "Hardware",
            "priority": "Medium",
            "department": "Maintenance",
            "status": "Open"
        },
        {
            "category": "Unclassified",
            "priority": "Unassigned",
            "department": "Unassigned",
            "status": "In Progress"
        }
    ]

    summary = generate_dashboard_summary(tickets)

    assert summary["total_tickets"] == 3
    assert summary["classified_tickets"] == 2
    assert summary["unclassified_tickets"] == 1


def test_dashboard_counts_resolved_and_outstanding_tickets():
    tickets = [
        {"status": "Resolved"},
        {"status": "Open"},
        {"status": "In Progress"}
    ]

    summary = generate_dashboard_summary(tickets)

    assert summary["resolved_tickets"] == 1
    assert summary["outstanding_tickets"] == 2


def test_dashboard_calculates_resolution_rate():
    tickets = [
        {"status": "Resolved"},
        {"status": "Resolved"},
        {"status": "Open"},
        {"status": "In Progress"}
    ]

    summary = generate_dashboard_summary(tickets)

    assert summary["resolution_rate"] == 50.0


def test_dashboard_counts_categories_priorities_and_departments():
    tickets = [
        {
            "category": "Network",
            "priority": "High",
            "department": "ICT"
        },
        {
            "category": "Network",
            "priority": "Low",
            "department": "ICT"
        },
        {
            "category": "Hardware",
            "priority": "High",
            "department": "Maintenance"
        }
    ]

    summary = generate_dashboard_summary(tickets)

    assert summary["categories"]["Network"] == 2
    assert summary["categories"]["Hardware"] == 1
    assert summary["priorities"]["High"] == 2
    assert summary["departments"]["ICT"] == 2


def test_department_resolution_performance():
    tickets = [
        {
            "department": "ICT",
            "status": "Resolved"
        },
        {
            "department": "ICT",
            "status": "Open"
        },
        {
            "department": "Maintenance",
            "status": "Resolved"
        }
    ]

    summary = generate_dashboard_summary(tickets)

    assert summary["department_resolution"]["ICT"] == {
        "total_tickets": 2,
        "resolved_tickets": 1,
        "resolution_rate": 50.0
    }

    assert summary["department_resolution"]["Maintenance"] == {
        "total_tickets": 1,
        "resolved_tickets": 1,
        "resolution_rate": 100.0
    }


def test_empty_ticket_list_returns_zero_statistics():
    summary = generate_dashboard_summary([])

    assert summary["total_tickets"] == 0
    assert summary["classified_tickets"] == 0
    assert summary["unclassified_tickets"] == 0
    assert summary["resolved_tickets"] == 0
    assert summary["outstanding_tickets"] == 0
    assert summary["resolution_rate"] == 0
