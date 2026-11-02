import json
import os
import re
from functools import lru_cache

from google import genai


# =====================================================
# GEMINI CONFIGURATION
# =====================================================

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-flash-latest")


@lru_cache(maxsize=1)
def create_gemini_client(api_key):
    """Create and reuse the Gemini client."""
    return genai.Client(api_key=api_key)


def get_gemini_client():
    """Retrieve the Gemini client using the configured API key."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Configure your Gemini API key."
        )

    return create_gemini_client(api_key)


def generate_response(prompt, temperature=0.4):
    """Send a prompt to Gemini and return its text response."""
    client = get_gemini_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "temperature": temperature,
            "max_output_tokens": 1800,
        }
    )

    result = response.text

    if not result:
        raise ValueError("Gemini returned an empty response.")

    return result.strip()


# =====================================================
# JSON EXTRACTION
# =====================================================

def extract_json(response_text):
    """Extract a JSON object from Gemini's response."""

    cleaned = response_text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("Gemini did not return valid JSON.")

    return json.loads(cleaned[start:end + 1])


# =====================================================
# MODULE 1: TICKET INTELLIGENCE
# =====================================================

def get_ticket_intelligence(description):
    """
    Analyse a campus support problem.

    Returns:
        category
        priority
        department
        reason
        recommended_action
    """

    if not description or not description.strip():
        return None

    prompt = f"""
You are the CampusFlow Ticket Intelligence Engine.

You analyse university and campus support problems.

Analyse the following problem carefully:

TICKET DESCRIPTION:
{description.strip()}

Choose exactly one category from:
- Network
- Hardware
- Software
- Facilities
- Other

Choose exactly one priority from:
- Critical
- High
- Medium
- Low

Identify the most appropriate responsible department.

Priority guidelines:

CRITICAL:
Immediate danger, serious security incident, major outage
or a problem affecting essential campus operations.

HIGH:
A serious problem affecting multiple students or an
important university service.

MEDIUM:
A problem affecting an individual or a limited group
but not causing an emergency.

LOW:
Minor inconvenience, general request or non-urgent issue.

Return ONLY a valid JSON object in this structure:

{{
    "category": "Network",
    "priority": "High",
    "department": "ICT Department",
    "reason": "Explain why this category and priority were selected.",
    "recommended_action": "Explain the immediate recommended action."
}}

Rules:
- Do not invent facts that are not in the description.
- Do not exaggerate the urgency.
- Explain your classification clearly.
- Return valid JSON only.
"""

    try:
        raw_response = generate_response(
            prompt,
            temperature=0.2
        )

        result = extract_json(raw_response)

        allowed_categories = {
            "Network",
            "Hardware",
            "Software",
            "Facilities",
            "Other"
        }

        allowed_priorities = {
            "Critical",
            "High",
            "Medium",
            "Low"
        }

        category = str(result.get("category", "Other")).strip()
        priority = str(result.get("priority", "Medium")).strip()

        if category not in allowed_categories:
            category = "Other"

        if priority not in allowed_priorities:
            priority = "Medium"

        return {
            "category": category,
            "priority": priority,
            "department": str(
                result.get("department", "General Support")
            ),
            "reason": str(
                result.get("reason", "No explanation provided.")
            ),
            "recommended_action": str(
                result.get(
                    "recommended_action",
                    "Refer the issue to the appropriate support department."
                )
            )
        }

    except Exception as error:
        print(f"Ticket intelligence error: {error}")
        return None


# =====================================================
# MODULE 2: AI SUGGESTIONS
# =====================================================

def get_ai_suggestions(description):
    """
    Generate practical troubleshooting recommendations
    for a campus support problem.
    """

    if not description or not description.strip():
        return "Please describe the problem so I can provide suggestions."

    prompt = f"""
You are the CampusFlow AI Troubleshooting Specialist.

Your responsibility is to help students, lecturers,
administrators and university support staff resolve campus problems.

PROBLEM:
{description.strip()}

Provide a useful, practical response using this structure:

## 1. Understanding the Problem
Briefly explain what may be happening.

## 2. Possible Causes
Identify the most likely causes.
Do not claim that an unverified cause is certain.

## 3. Recommended Solutions
Give at least three numbered troubleshooting steps.

Each step must:
- Be clear and practical.
- Explain exactly what the user should do.
- Be suitable for a non-technical student where possible.

## 4. When to Escalate
Explain when the user should contact the responsible
university department and what information to provide.

## 5. Prevention
Give practical advice to reduce the chance of the
problem happening again.

IMPORTANT RULES:
- Never request passwords or private login credentials.
- Never recommend bypassing university security.
- Never claim that you have fixed the problem.
- Do not invent university policies or contact details.
- If the issue involves electrical danger, physical danger
  or an urgent security incident, advise the user to contact
  the appropriate university emergency or support personnel.
- Keep the response professional and easy to understand.
"""

    try:
        return generate_response(
            prompt,
            temperature=0.5
        )

    except Exception as error:
        print(f"AI suggestions error: {error}")

        return (
            "CampusFlow AI could not generate suggestions right now. "
            "Please check your Gemini API configuration and try again."
        )


# =====================================================
# MODULE 3: CAMPUSFLOW CHATBOT
# =====================================================

def prepare_ticket_context(tickets):
    """Prepare a safe, concise summary of recent ticket records."""

    if not tickets:
        return "No ticket records are currently available."

    summaries = []

    for ticket in tickets[-10:]:

        if not isinstance(ticket, dict):
            continue

        summary = {
            "ticket_id": ticket.get(
                "ticket_id",
                ticket.get("id", "Unknown")
            ),
            "title": ticket.get("title", "Untitled"),
            "description": ticket.get("description", ""),
            "category": ticket.get("category", "Unclassified"),
            "priority": ticket.get("priority", "Unassigned"),
            "status": ticket.get("status", "Unknown"),
            "department": ticket.get("department", "Unassigned")
        }

        summaries.append(summary)

    return json.dumps(
        summaries,
        indent=2,
        ensure_ascii=False
    )


def get_chatbot_response(messages, tickets=None):
    """
    Generate a context-aware chatbot response.

    Uses recent conversation history and available ticket records.
    """

    if not messages:
        return "Hello! How can I help you with campus support today?"

    ticket_context = prepare_ticket_context(tickets)

    conversation = []

    for message in messages[-8:]:

        if not isinstance(message, dict):
            continue

        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()

        if not content:
            continue

        if role not in {"user", "assistant"}:
            continue

        conversation.append(
            f"{role.upper()}: {content[:2000]}"
        )

    conversation_history = "\n\n".join(conversation)

    prompt = f"""
You are CampusFlow AI, an intelligent university campus
support assistant.

YOUR RESPONSIBILITIES:
1. Answer campus support questions.
2. Explain ticket creation and management.
3. Help users understand ticket priorities and statuses.
4. Provide practical troubleshooting guidance.
5. Use available ticket records to answer relevant questions.
6. Help users understand which support department may be responsible.

AVAILABLE CAMPUS TICKET RECORDS:
{ticket_context}

RECENT CONVERSATION:
{conversation_history}

IMPORTANT RULES:

- Be friendly, professional and helpful.
- Give direct answers before adding explanations.
- Use the available ticket records when relevant.
- Never invent ticket IDs or ticket information.
- Never claim to have created, updated, assigned or resolved a ticket.
- You may explain how a user can perform those actions in CampusFlow.
- Never request passwords or sensitive login credentials.
- If information is unavailable, say so honestly.
- Keep answers organised and easy to understand.
- Remember the context of the conversation when answering follow-up questions.

Respond to the latest user message.
"""

    try:
        return generate_response(
            prompt,
            temperature=0.6
        )

    except Exception as error:
        print(f"CampusFlow chatbot error: {error}")

        return (
            "I'm sorry, CampusFlow AI is temporarily unable to respond. "
            "Please check the Gemini API configuration and try again."
        )
