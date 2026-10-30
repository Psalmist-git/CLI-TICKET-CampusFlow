# Validate ticket title
def get_ticket_title():
    title = ""

    while title == "":
        title = input("Enter Ticket Title: ").strip()

        if title == "":
            print("Error: Ticket title cannot be empty. Try again.")

    return title


# Validate ticket description
def get_ticket_description():
    description = ""

    while description == "":
        description = input("Enter ticket description: ").strip()

        if description == "":
            print("Error: Ticket description cannot be empty. Try again.")

    return description