import os
import json
import time
from functools import lru_cache
from google import genai


# =====================================================
# GEMINI MODEL CONFIGURATION
# =====================================================

# Keep separate model settings for independent optimisation.
ANALYSIS_MODEL_NAME = "gemini-3.1-flash-lite"
CHAT_MODEL_NAME = "gemini-3.1-flash-lite"


# =====================================================
# GEMINI CLIENT
# =====================================================

@lru_cache(maxsize=1)
def create_gemini_client(api_key):
    """Create and reuse a Gemini client."""

    return genai.Client(api_key=api_key)


def get_gemini_client():
    """Get the reusable Gemini client."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return create_gemini_client(api_key)


# =====================================================
# SMART TICKET CLASSIFICATION
# =====================================================

def get_ticket_intelligence(description):
    """Classify a campus support ticket quickly."""

    start_time = time.perf_counter()

    try:
        client = get_gemini_client()

        if not client:
            return None

        prompt = f"""
Classify this campus support ticket.

DESCRIPTION:
{description}

CATEGORY:
Network, Hardware, Software, Facilities, Other.

PRIORITY:
Critical, High, Medium, Low.

DEPARTMENT:
Recommend the appropriate campus support department.

REASON:
Briefly explain the classification.

RULES:
- Use only facts supported by the description.
- Reserve Critical for genuinely urgent issues.
- If information is insufficient, explain why.
- Return valid JSON only.
- Do not include markdown.

FORMAT:
{{
    "category": "",
    "priority": "",
    "department": "",
    "reason": ""
}}
"""

        response = client.interactions.create(
            model=ANALYSIS_MODEL_NAME,
            input=prompt
        )

        if not response.output_text:
            return None

        intelligence = json.loads(response.output_text)

        required_fields = [
            "category",
            "priority",
            "department",
            "reason"
        ]

        if not all(field in intelligence for field in required_fields):
            return None

        result = {
            field: str(intelligence[field])
            for field in required_fields
        }

        elapsed_time = time.perf_counter() - start_time

        print(
            f"CampusFlow classification time: {elapsed_time:.2f} seconds"
        )

        return result

    except Exception as error:

        elapsed_time = time.perf_counter() - start_time

        print(
            f"AI intelligence error: {type(error).__name__}"
        )

        print(
            f"Classification failed after: {elapsed_time:.2f} seconds"
        )

        return None


# =====================================================
# AI TROUBLESHOOTING SUGGESTIONS
# =====================================================

def get_ai_suggestions(description):
    """Generate concise troubleshooting suggestions quickly."""

    start_time = time.perf_counter()

    try:
        client = get_gemini_client()

        if not client:
            return "AI unavailable: Gemini API key is missing."

        prompt = f"""
You are a campus IT support assistant.

Analyse this ticket:

{description}

Give a concise response with:

1. Likely cause.
2. Three practical troubleshooting steps.
3. When to escalate to a technician.
4. Up to two questions if more information is needed.

RULES:
- Be practical and specific.
- Do not invent facts.
- Avoid unnecessary explanations.
- Keep the response concise.
"""

        response = client.interactions.create(
            model=ANALYSIS_MODEL_NAME,
            input=prompt
        )

        if not response.output_text:
            return "AI could not generate suggestions."

        elapsed_time = time.perf_counter() - start_time

        print(
            f"CampusFlow suggestions time: {elapsed_time:.2f} seconds"
        )

        return response.output_text

    except Exception as error:

        elapsed_time = time.perf_counter() - start_time

        print(
            f"AI suggestions error: {type(error).__name__}"
        )

        print(
            f"Suggestions failed after: {elapsed_time:.2f} seconds"
        )

        return "Sorry, AI suggestions are currently unavailable."


# =====================================================
# CAMPUSFLOW AI CHATBOT
# PRESERVED WITHOUT CHANGES
# =====================================================

def get_chatbot_response(messages, tickets=None):
    """
    Generate a conversational response using the faster Gemini model.

    messages:
        List of dictionaries containing role and content.

    tickets:
        Saved CampusFlow ticket records.
    """

    start_time = time.perf_counter()

    try:

        client = get_gemini_client()

        if not client:
            return (
                "The AI assistant is unavailable because "
                "the Gemini API key is missing."
            )

        # -------------------------------------------------
        # 1. PREPARE RECENT TICKET INFORMATION
        # -------------------------------------------------

        ticket_context = "No ticket records are available."

        if tickets:

            recent_tickets = tickets[-10:]

            ticket_lines = []

            for ticket in recent_tickets:

                ticket_lines.append(
                    f"ID: {ticket.get('id', 'Unknown')} | "
                    f"Title: {ticket.get('title', 'Untitled')} | "
                    f"Category: {ticket.get('category', 'Unclassified')} | "
                    f"Priority: {ticket.get('priority', 'Unassigned')} | "
                    f"Department: {ticket.get('department', 'Unassigned')} | "
                    f"Status: {ticket.get('status', 'Open')}"
                )

            ticket_context = "\n".join(ticket_lines)

        # -------------------------------------------------
        # 2. REDUCE CONVERSATION HISTORY
        # -------------------------------------------------

        recent_messages = messages[-8:]

        conversation = []

        for message in recent_messages:

            role = message.get("role", "user")
            content = message.get("content", "")

            if role not in ("user", "assistant"):
                continue

            role_name = (
                "CampusFlow AI"
                if role == "assistant"
                else "User"
            )

            conversation.append(
                f"{role_name}: {content}"
            )

        conversation_text = "\n".join(conversation)

        # -------------------------------------------------
        # 3. BUILD A SHORTER PROMPT
        # -------------------------------------------------

        prompt = f"""
You are CampusFlow AI, a friendly university campus support assistant.

YOUR JOB:
- Help students and staff with campus support problems.
- Provide practical troubleshooting advice.
- Explain ticket creation, statuses and priorities.
- Answer questions about available campus tickets.

RULES:
- Use the ticket records below when answering ticket questions.
- Never invent ticket IDs, statistics or department information.
- If information is unavailable, say so.
- Do not claim to create or update tickets.
- Never request passwords or sensitive personal information.
- Keep answers clear, helpful and concise.
- For emergencies, advise contacting campus emergency services.

RECENT CAMPUS TICKETS:
{ticket_context}

RECENT CONVERSATION:
{conversation_text}

Answer the user's latest message directly.
"""

        # -------------------------------------------------
        # 4. SEND REQUEST TO THE LIGHTWEIGHT MODEL
        # -------------------------------------------------

        response = client.interactions.create(
            model=CHAT_MODEL_NAME,
            input=prompt
        )

        if not response.output_text:
            return "I couldn't generate a response. Please try again."

        answer = response.output_text

        # -------------------------------------------------
        # 5. MEASURE RESPONSE TIME
        # -------------------------------------------------

        elapsed_time = time.perf_counter() - start_time

        print(
            f"CampusFlow AI response time: {elapsed_time:.2f} seconds"
        )

        return answer

    except Exception as error:

        elapsed_time = time.perf_counter() - start_time

        print(
            f"Chatbot error: {type(error).__name__}"
        )

        print(
            f"Failed request time: {elapsed_time:.2f} seconds"
        )

        return (
            "I'm sorry, the CampusFlow AI Assistant is temporarily "
            "unavailable. Please try again shortly."
        )
