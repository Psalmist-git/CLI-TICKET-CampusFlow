import json
import logging
import os
import re
import urllib.error
import urllib.request
from functools import lru_cache

import streamlit as st
from google import genai
from groq import Groq


# =====================================================
# LOGGING
# =====================================================

logger = logging.getLogger("campusflow.ai")

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )


# =====================================================
# AI PROVIDER CONFIGURATION
# =====================================================

PROVIDERS = {
    "Gemini": {
        "key": "GEMINI_API_KEY",
        "environment_variable": "GEMINI_API_KEY",
        "models": [
            "gemini-3.8-flash",
            "gemini-flash-latest",
        ],
        "default": "gemini-3.8-flash",
        "default_model": "gemini-3.8-flash",
    },

    "Groq": {
        "key": "GROQ_API_KEY",
        "environment_variable": "GROQ_API_KEY",
        "models": [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
        ],
        "default": "openai/gpt-oss-120b",
        "default_model": "openai/gpt-oss-120b",
    },

    
    "OpenRouter": {
        "key": "OPENROUTER_API_KEY",
        "environment_variable": "OPENROUTER_API_KEY",
        "models": [
            "openai/gpt-oss-120b",
            "anthropic/claude-sonnet-4-6",
            "google/gemini-3.8-flash",
        ],
        "default": "openai/gpt-oss-120b",
        "default_model": "openai/gpt-oss-120b",
    },
}

DEFAULT_PROVIDER = "Gemini"


# =====================================================
# API KEY MANAGEMENT
# =====================================================

def get_setting(name):
    """Read a setting securely from environment or Streamlit secrets."""

    value = os.getenv(name)

    if value:
        return value

    try:
        return st.secrets[name]
    except Exception:
        return None


def get_selected_provider():

    provider = st.session_state.get(
        "ai_provider",
        DEFAULT_PROVIDER
    )

    if provider not in PROVIDERS:
        return DEFAULT_PROVIDER

    return provider


def get_selected_model():

    provider = get_selected_provider()
    config = PROVIDERS[provider]

    model = st.session_state.get(
        f"ai_model_{provider}",
        config["default_model"]
    )

    if model not in config["models"]:
        return config["default_model"]

    return model


# =====================================================
# SAFE ERROR DIAGNOSTICS
# =====================================================

def safe_error_text(message):
    """
    Remove configured API keys from error messages
    before writing diagnostic information to logs.
    """

    text = str(message)

    for key_name in (
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
    ):
        secret = get_setting(key_name)

        if secret:
            text = text.replace(str(secret), "[REDACTED]")

    return text[:2000]


def extract_provider_error(error_body):
    """Extract a readable error message from provider JSON."""

    try:
        data = json.loads(error_body)

        error = data.get("error", data)

        if isinstance(error, dict):
            message = (
                error.get("message")
                or error.get("detail")
                or error.get("type")
            )

            if message:
                return str(message)

        return json.dumps(data)[:1500]

    except (json.JSONDecodeError, TypeError):
        return str(error_body)[:1500]


# =====================================================
# SIDEBAR AI PROVIDER SELECTOR
# =====================================================

def render_ai_provider_selector():

    st.markdown("### 🤖 AI Configuration")

    provider_names = list(PROVIDERS.keys())

    current_provider = get_selected_provider()

    provider = st.selectbox(
        "Choose AI Provider",
        provider_names,
        index=provider_names.index(current_provider),
        key="ai_provider"
    )

    config = PROVIDERS[provider]

    model_key = f"ai_model_{provider}"

    current_model = st.session_state.get(
        model_key,
        config["default_model"]
    )

    if current_model not in config["models"]:
        current_model = config["default_model"]

    st.selectbox(
        "Choose AI Model",
        config["models"],
        index=config["models"].index(current_model),
        key=model_key
    )

    api_key = get_setting(config["environment_variable"])

    if api_key:
        st.success(f"{provider} API key configured")
    else:
        st.warning(f"{provider} API key not configured")

    st.caption(
        "Your selected provider powers ticket intelligence, "
        "troubleshooting and the CampusFlow chatbot."
    )


# =====================================================
# GEMINI
# =====================================================

@lru_cache(maxsize=4)
def create_gemini_client(api_key):

    return genai.Client(api_key=api_key)


def generate_gemini_response(prompt, model, temperature):

    api_key = get_setting("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    client = create_gemini_client(api_key)

    models_to_try = list(dict.fromkeys([
        model,
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
    ]))

    last_error = None

    for selected_model in models_to_try:

        try:
            response = client.models.generate_content(
                model=selected_model,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": 1800,
                }
            )

            result = response.text

            if result:
                logger.info("Gemini succeeded using %s", selected_model)
                return result.strip()

            last_error = ValueError("Gemini returned an empty response.")

        except Exception as error:
            last_error = error

            logger.warning(
                "Gemini model failed: %s | %s",
                selected_model,
                safe_error_text(error)
            )

    raise RuntimeError(
        f"All Gemini models failed: {safe_error_text(last_error)}"
    )


# =====================================================
# GROQ AND OPENROUTER
# =====================================================

def generate_groq_response(prompt, model, temperature):
    api_key = get_setting("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key is not configured.")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=temperature,
        max_tokens=1800,
    )

    answer = response.choices[0].message.content

    if not answer:
        raise ValueError("Groq returned an empty response.")

    return answer.strip()


def generate_openai_compatible_response(
    prompt,
    provider,
    model,
    temperature
):
    api_key = get_setting("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError("OpenRouter API key is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://cli-ticket-campusflow.onrender.com",
        "X-Title": "CampusFlow",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": temperature,
        "max_tokens": 1800,
    }

    return send_api_request(
        "https://openrouter.ai/api/v1/chat/completions",
        headers,
        payload,
        "OpenRouter"
    )


# =====================================================
# CLAUDE
# =====================================================

def generate_claude_response(prompt, model, temperature):

    api_key = get_setting("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError(
            "Claude API key is not configured."
        )

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "max_tokens": 1800,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
    }

    return send_api_request(
        "https://api.anthropic.com/v1/messages",
        headers,
        payload,
        "Claude"
    )


# =====================================================
# SHARED HTTP REQUEST HANDLER
# =====================================================

def send_api_request(url, headers, payload, provider):

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=90
        ) as response:

            response_body = response.read().decode("utf-8")

            result = json.loads(response_body)

    except urllib.error.HTTPError as error:

        error_body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        provider_message = extract_provider_error(
            error_body
        )

        diagnostic = safe_error_text(provider_message)

        raise RuntimeError(
            f"{provider} API returned HTTP {error.code}: "
            f"{diagnostic}"
        ) from None

    except urllib.error.URLError as error:

        reason = safe_error_text(error.reason)

        raise RuntimeError(
            f"{provider} connection failed: {reason}"
        ) from None

    except TimeoutError:

        raise RuntimeError(
            f"{provider} request timed out after 90 seconds."
        ) from None

    except json.JSONDecodeError:

        raise RuntimeError(
            f"{provider} returned an invalid JSON response."
        ) from None

    # Extract Claude response.
    if provider == "Claude":

        content = result.get("content", [])

        text_parts = [
            item.get("text", "")
            for item in content
            if item.get("type") == "text"
        ]

        answer = "\n".join(text_parts)

    # Extract Groq and OpenRouter responses.
    else:

        choices = result.get("choices", [])

        if not choices:
            raise ValueError(
                f"{provider} returned no response choices."
            )

        answer = (
            choices[0]
            .get("message", {})
            .get("content", "")
        )

    if not answer:
        raise ValueError(
            f"{provider} returned an empty response."
        )

    return answer.strip()


# =====================================================
# UNIVERSAL AI RESPONSE ENGINE
# =====================================================


def generate_response(
    prompt,
    temperature=0.4,
    provider=None,
    model=None
):

    provider = provider or get_selected_provider()

    if provider not in PROVIDERS:
        raise ValueError("Unsupported AI provider.")

    if model is None:
        model = st.session_state.get(
            f"ai_model_{provider}",
            PROVIDERS[provider]["default_model"]
        )

    if model not in PROVIDERS[provider]["models"]:
        model = PROVIDERS[provider]["default_model"]

    logger.info(
        "AI request started | provider=%s | model=%s",
        provider,
        model
    )

    try:

        if provider == "Gemini":
            answer = generate_gemini_response(
                prompt, model, temperature
            )

        elif provider == "Groq":
            answer = generate_groq_response(
                prompt, model, temperature
            )

        elif provider == "OpenRouter":
            answer = generate_openai_compatible_response(
                prompt, provider, model, temperature
            )

        else:
            raise ValueError("Unsupported AI provider selected.")

        logger.info(
            "AI request successful | provider=%s | model=%s",
            provider,
            model
        )

        return answer

    except Exception as error:
        diagnostic = safe_error_text(error)

        logger.error(
            "AI request failed | provider=%s | model=%s | error=%s",
            provider,
            model,
            diagnostic,
            exc_info=True
        )

        raise


# =====================================================
# JSON EXTRACTION
# =====================================================

def extract_json(response_text):

    cleaned = response_text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "The AI did not return valid JSON."
        )

    return json.loads(
        cleaned[start:end + 1]
    )


# =====================================================
# MODULE 1: TICKET INTELLIGENCE
# =====================================================

def get_ticket_intelligence(
    description,
    provider=None,
    model=None
):

    if not description or not description.strip():
        return None

    prompt = f"""
You are the CampusFlow Ticket Intelligence Engine.

Analyse this university or campus support problem:

TICKET DESCRIPTION:
{description.strip()}

Choose exactly one category:
Network, Hardware, Software, Facilities, Other.

Choose exactly one priority:
Critical, High, Medium, Low.

Identify the responsible department.

Priority guidelines:

CRITICAL:
Immediate danger, serious security incident, major outage
or essential campus operations affected.

HIGH:
Serious problem affecting multiple students or an
important university service.

MEDIUM:
Problem affecting an individual or limited group
without an emergency.

LOW:
Minor inconvenience or non-urgent request.

Return ONLY valid JSON:

{{
    "category": "Network",
    "priority": "High",
    "department": "ICT Department",
    "reason": "Explain the classification.",
    "recommended_action": "Explain the immediate action."
}}

Rules:
- Do not invent facts.
- Do not exaggerate urgency.
- Return valid JSON only.
"""

    try:

        raw_response = generate_response(
            prompt,
            temperature=0.2,
            provider=provider,
            model=model
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

        category = str(
            result.get("category", "Other")
        ).strip()

        priority = str(
            result.get("priority", "Medium")
        ).strip()

        if category not in allowed_categories:
            category = "Other"

        if priority not in allowed_priorities:
            priority = "Medium"

        return {
            "category": category,
            "priority": priority,
            "department": str(
                result.get(
                    "department",
                    "General Support"
                )
            ),
            "reason": str(
                result.get(
                    "reason",
                    "No explanation provided."
                )
            ),
            "recommended_action": str(
                result.get(
                    "recommended_action",
                    "Refer to the appropriate support department."
                )
            )
        }

    except Exception as error:

        logger.error(
            "Ticket intelligence failed: %s",
            safe_error_text(error)
        )

        return None


# =====================================================
# MODULE 2: AI TROUBLESHOOTING SUGGESTIONS
# =====================================================

def get_ai_suggestions(
    description,
    provider=None,
    model=None
):

    if not description or not description.strip():
        return "Please describe the problem first."

    prompt = f"""
You are the CampusFlow AI Troubleshooting Specialist.

PROBLEM:
{description.strip()}

Provide a practical response using this structure:

## 1. Understanding the Problem
Explain what may be happening.

## 2. Possible Causes
Identify likely causes without presenting guesses as facts.

## 3. Recommended Solutions
Give at least three numbered troubleshooting steps.
Make each step practical and easy to follow.

## 4. When to Escalate
Explain when the user should contact the responsible
university department and what information to provide.

## 5. Prevention
Give practical advice to prevent recurrence.

IMPORTANT:
- Never request passwords or private credentials.
- Never recommend bypassing university security.
- Never claim you have fixed the problem.
- Do not invent university policies or contact details.
- Escalate physical danger and urgent security incidents
  to appropriate university personnel.
- Use clear, professional language.
"""

    try:

        return generate_response(
            prompt,
            temperature=0.5,
            provider=provider,
            model=model
        )

    except Exception as error:

        logger.error(
            "AI suggestions failed: %s",
            safe_error_text(error)
        )

        return (
            "CampusFlow could not generate suggestions. "
            "Please check the selected provider and try again."
        )


# =====================================================
# MODULE 3: CAMPUSFLOW CHATBOT
# =====================================================

def prepare_ticket_context(tickets):

    if not tickets:
        return (
            "No ticket records are currently available."
        )

    summaries = []

    for ticket in tickets[-10:]:

        if not isinstance(ticket, dict):
            continue

        summaries.append({
            "ticket_id": ticket.get(
                "ticket_id",
                ticket.get("id", "Unknown")
            ),
            "title": ticket.get(
                "title",
                "Untitled"
            ),
            "description": ticket.get(
                "description",
                ""
            ),
            "category": ticket.get(
                "category",
                "Unclassified"
            ),
            "priority": ticket.get(
                "priority",
                "Unassigned"
            ),
            "status": ticket.get(
                "status",
                "Unknown"
            ),
            "department": ticket.get(
                "department",
                "Unassigned"
            )
        })

    return json.dumps(
        summaries,
        indent=2,
        ensure_ascii=False
    )


def get_chatbot_response(
    messages,
    tickets=None,
    provider=None,
    model=None
):

    if not messages:
        return (
            "Hello! How can I help you with campus support today?"
        )

    ticket_context = prepare_ticket_context(tickets)

    conversation = []

    for message in messages[-8:]:

        if not isinstance(message, dict):
            continue

        role = message.get("role", "user")

        content = str(
            message.get("content", "")
        ).strip()

        if not content:
            continue

        if role not in {"user", "assistant"}:
            continue

        conversation.append(
            f"{role.upper()}: {content[:2000]}"
        )

    conversation_history = "\n\n".join(
        conversation
    )

    prompt = f"""
You are CampusFlow AI, an intelligent university campus
support assistant.

YOUR RESPONSIBILITIES:
1. Answer campus support questions.
2. Explain ticket creation and management.
3. Explain ticket priorities and statuses.
4. Provide practical troubleshooting guidance.
5. Use available ticket records when relevant.
6. Explain which support department may be responsible.

AVAILABLE CAMPUS TICKET RECORDS:
{ticket_context}

RECENT CONVERSATION:
{conversation_history}

IMPORTANT RULES:
- Be friendly, professional and helpful.
- Give direct answers before explanations.
- Never invent ticket IDs or ticket information.
- Never claim to have created, updated, assigned or
  resolved a ticket.
- Explain how users can perform those actions.
- Never request passwords or sensitive credentials.
- If information is unavailable, say so honestly.
- Keep answers organised and easy to understand.
- Remember the conversation context.

Respond to the latest user message.
"""

    try:

        return generate_response(
            prompt,
            temperature=0.6,
            provider=provider,
            model=model
        )

    except Exception as error:

        logger.error(
            "CampusFlow chatbot failed: %s",
            safe_error_text(error)
        )

        return (
            "CampusFlow AI could not complete your request. "
            "The technical error has been recorded. "
            "Please try again shortly."
        )