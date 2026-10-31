# Import functions from our other modules
from storage import load_tickets, save_tickets
from ticket_manager import generate_ticket_id
from validation import get_ticket_title, get_ticket_description
from ai_assistant import get_ai_suggestions

# 1. Welcome messages
print("*************************************************")
print("         CAMPUSFLOW TICKET CREATOR")
print("*************************************************")

print("Welcome Buddy! Let's create a new ticket.")


# 2. Collect and validate ticket title
title = get_ticket_title()

print("Ticket title accepted:", title)


# 3. Collect and validate ticket description
description = get_ticket_description()

print("Description accepted:", description)


# 4. Load existing tickets
tickets = load_tickets()


# 5. Generate the next ticket ID
ticket_id = generate_ticket_id(tickets)


# 6. Create a ticket dictionary
ticket = {
    "id": ticket_id,
    "title": title,
    "description": description
}


# 7. Add the new ticket to the list
tickets.append(ticket)


# 8. Save all tickets
save_tickets(tickets)


# 9. Display the created ticket
print("\nTicket created successfully!")
print("Ticket ID:", ticket["id"])
print("Ticket Title:", ticket["title"])
print("Description:", ticket["description"])


# 10. Display all retrieved tickets
saved_tickets = load_tickets()
print("\nGetting AI suggestions...")

suggestions = get_ai_suggestions(ticket["description"])

print("\nAI Suggestions:")
print(suggestions)

print("\nAll Retrieved Tickets:")
print(saved_tickets)
