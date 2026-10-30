import json


# Load existing tickets
def load_tickets():
    try:
        with open("tickets.json", "r") as file:
            tickets = json.load(file)

            if isinstance(tickets, list):
                return tickets

            print("Warning: Ticket data must be a list.")
            raise SystemExit

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        print("Error: tickets.json is damaged or contains invalid JSON.")
        raise SystemExit


# Save all tickets
def save_tickets(tickets):
    with open("tickets.json", "w") as file:
        json.dump(tickets, file, indent=4)
