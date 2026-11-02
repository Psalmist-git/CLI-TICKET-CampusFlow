import re
from difflib import SequenceMatcher


def clean_text(text):
    """Convert text to lowercase and remove punctuation."""
    text = text.lower()
    words = re.findall(r"\b[a-z0-9]+\b", text)

    ignored_words = {
        "the", "is", "a", "an", "and", "or", "in",
        "on", "at", "to", "of", "for", "my", "it",
        "has", "have", "been", "are", "was", "with"
    }

    return {
        word for word in words
        if word not in ignored_words
    }


def calculate_similarity(new_ticket, existing_ticket):
    """Calculate how similar two ticket descriptions are."""

    new_text = (
        new_ticket.get("title", "") + " " +
        new_ticket.get("description", "")
    ).lower()

    existing_text = (
        existing_ticket.get("title", "") + " " +
        existing_ticket.get("description", "")
    ).lower()

    new_words = clean_text(new_text)
    existing_words = clean_text(existing_text)

    # Avoid comparing empty descriptions
    if not new_words or not existing_words:
        return 0

    # Compare the words shared by both tickets
    common_words = new_words.intersection(existing_words)
    all_words = new_words.union(existing_words)

    keyword_similarity = len(common_words) / len(all_words)

    # Compare the overall wording
    wording_similarity = SequenceMatcher(
        None,
        new_text,
        existing_text
    ).ratio()

    # Combine both similarity measurements
    similarity = (
        0.7 * keyword_similarity +
        0.3 * wording_similarity
    )

    return similarity


def find_possible_duplicates(new_ticket, existing_tickets):
    """Find existing tickets that may describe the same problem."""

    possible_duplicates = []

    for ticket in existing_tickets:

        similarity = calculate_similarity(
            new_ticket,
            ticket
        )

        if similarity >= 0.35:
            possible_duplicates.append({
                "id": ticket.get("id", "Unknown"),
                "title": ticket.get("title", "Untitled"),
                "category": ticket.get("category", "Unclassified"),
                "similarity": round(similarity * 100, 1)
            })

    # Show the most similar tickets first
    possible_duplicates.sort(
        key=lambda ticket: ticket["similarity"],
        reverse=True
    )

    return possible_duplicates
