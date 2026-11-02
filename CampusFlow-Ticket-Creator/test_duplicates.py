from duplicate_detector import (
    clean_text,
    calculate_similarity,
    find_possible_duplicates
)


def test_identical_tickets_are_detected():
    new_ticket = {
        "title": "Library Wi-Fi Problem",
        "description": "The library Wi-Fi is not working."
    }

    existing_tickets = [
        {
            "id": "TKT-001",
            "title": "Library Wi-Fi Problem",
            "description": "The library Wi-Fi is not working.",
            "category": "Network"
        }
    ]

    duplicates = find_possible_duplicates(
        new_ticket,
        existing_tickets
    )

    assert len(duplicates) == 1
    assert duplicates[0]["id"] == "TKT-001"
    assert duplicates[0]["similarity"] == 100.0


def test_unrelated_tickets_are_not_detected():
    new_ticket = {
        "title": "Library Wi-Fi Problem",
        "description": "The library internet connection is broken."
    }

    existing_tickets = [
        {
            "id": "TKT-002",
            "title": "Broken Classroom Projector",
            "description": "The projector bulb needs replacement.",
            "category": "Hardware"
        }
    ]

    duplicates = find_possible_duplicates(
        new_ticket,
        existing_tickets
    )

    assert duplicates == []


def test_empty_ticket_text_has_zero_similarity():
    new_ticket = {
        "title": "",
        "description": ""
    }

    existing_ticket = {
        "title": "",
        "description": ""
    }

    similarity = calculate_similarity(
        new_ticket,
        existing_ticket
    )

    assert similarity == 0


def test_duplicate_results_are_sorted_by_similarity():
    new_ticket = {
        "title": "Library Wi-Fi Problem",
        "description": "The library Wi-Fi is not working."
    }

    existing_tickets = [
        {
            "id": "TKT-001",
            "title": "Library Wi-Fi Problem",
            "description": "The library Wi-Fi is not working.",
            "category": "Network"
        },
        {
            "id": "TKT-002",
            "title": "Library Internet Problem",
            "description": "The library internet is unavailable.",
            "category": "Network"
        }
    ]

    duplicates = find_possible_duplicates(
        new_ticket,
        existing_tickets
    )

    similarities = [
        ticket["similarity"]
        for ticket in duplicates
    ]

    assert similarities == sorted(
        similarities,
        reverse=True
    )


def test_clean_text_removes_common_words_and_punctuation():
    result = clean_text("The Wi-Fi is not working in the Library!")

    assert "the" not in result
    assert "is" not in result
    assert "wi" in result
    assert "fi" in result
    assert "library" in result