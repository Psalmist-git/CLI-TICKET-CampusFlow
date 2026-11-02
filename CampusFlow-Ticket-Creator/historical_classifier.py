from concurrent.futures import ThreadPoolExecutor, as_completed
from ai_assistant import get_ticket_intelligence


def classify_unclassified_tickets(tickets, progress_callback=None):

    unclassified = [
        ticket for ticket in tickets
        if ticket.get("category", "Unclassified") == "Unclassified"
    ]

    total = len(unclassified)
    updated = 0
    failed = 0

    def analyse_ticket(ticket):
        description = ticket.get("description", "").strip()

        if not description:
            return ticket, None

        return ticket, get_ticket_intelligence(description)

    # Process up to 3 AI requests simultaneously
    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [
            executor.submit(analyse_ticket, ticket)
            for ticket in unclassified
        ]

        for index, future in enumerate(as_completed(futures), start=1):

            ticket, intelligence = future.result()

            if intelligence:
                ticket["category"] = intelligence["category"]
                ticket["priority"] = intelligence["priority"]
                ticket["department"] = intelligence["department"]
                ticket["reason"] = intelligence["reason"]
                updated += 1
            else:
                failed += 1

            if progress_callback:
                progress_callback(index, total)

    return tickets, updated, failed