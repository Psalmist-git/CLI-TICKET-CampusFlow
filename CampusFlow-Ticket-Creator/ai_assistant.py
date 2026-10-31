import os
from google import genai


def get_ai_suggestions(description):

    # Check whether the API key exists
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "AI unavailable: Gemini API key is missing."

    try:
        # Connect to Gemini
        client = genai.Client(api_key=api_key)

        # Prepare instructions for the AI
        prompt = f"""
        You are a campus IT support assistant.

        Analyse this ticket description:

        {description}

        Provide a targeted response using this format:

        1. Likely cause:
        2. Recommended actions:
           - Give 3 to 5 practical troubleshooting steps.
        3. Escalation:
           - Explain when the issue should be referred to a technician.

        Important instructions:
        - Base your response only on the information provided.
        - Do not invent details or assume facts that are not stated.
        - If the description is unclear or insufficient, say so.
        - Ask up to 3 relevant questions to clarify the problem.
        - Keep your response concise and practical.
        """

        # Send the prompt using the Interactions API
        response = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt
        )

        if not response.output_text:
            return "AI could not generate suggestions for this ticket."

        # Return the generated suggestions
        return response.output_text

    except Exception as error:
        print(f"AI service error: {type(error).__name__}")
        return "Sorry, AI suggestions are currently unavailable."