from storage import load_tickets
from reports import generate_dashboard_summary


# Load tickets from tickets.json
tickets = load_tickets()

# Generate dashboard statistics
summary = generate_dashboard_summary(tickets)

# Display results
print("\nCAMPUSFLOW INTELLIGENCE DASHBOARD")
print("----------------------------------")

print("Total Tickets:", summary["total_tickets"])
print("Classified Tickets:", summary["classified_tickets"])
print("Unclassified Tickets:", summary["unclassified_tickets"])

print("\nTickets by Category:")
for category, count in summary["categories"].items():
    print(category, ":", count)

print("\nTickets by Priority:")
for priority, count in summary["priorities"].items():
    print(priority, ":", count)

print("\nTickets by Department:")
for department, count in summary["departments"].items():
    print(department, ":", count)