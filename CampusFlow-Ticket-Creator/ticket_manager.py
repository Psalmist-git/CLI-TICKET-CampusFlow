# 2. Generate a unique ticket ID
def generate_ticket_id(tickets):
    highest_number = 0

    for ticket in tickets:
        ticket_id = ticket["id"]
        parts = ticket_id.split("-")
        number = int(parts[1])

        if number > highest_number:
            highest_number = number

    next_number = highest_number + 1

    return f"TKT-{next_number:03d}"