import json
import os
from pathlib import Path


# Local storage by default.
# Render will use /var/data when CAMPUSFLOW_DATA_DIR is configured.
DATA_DIR = Path(os.getenv("CAMPUSFLOW_DATA_DIR", "."))
TICKETS_FILE = DATA_DIR / "tickets.json"


# Load existing tickets
def load_tickets():
    try:
        with open(TICKETS_FILE, "r", encoding="utf-8") as file:
            tickets = json.load(file)

            if isinstance(tickets, list):
                # Give older tickets a default status
                for ticket in tickets:
                    if isinstance(ticket, dict):
                        ticket.setdefault("status", "Open")

                return tickets

            raise ValueError("Ticket data must be a list.")

    except FileNotFoundError:
        return []

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Error: {TICKETS_FILE} is damaged or contains invalid JSON."
        ) from error


# Save all tickets
def save_tickets(tickets):
    if not isinstance(tickets, list):
        raise ValueError("Tickets must be a list.")

    # Ensure storage directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Save safely using a temporary file
    temporary_file = TICKETS_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(tickets, file, indent=4)

    temporary_file.replace(TICKETS_FILE)