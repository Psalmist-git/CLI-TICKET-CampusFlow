from ai_assistant import get_ai_suggestions

description = "My laptop connects to campus Wi-Fi but websites do not load."

print("Getting AI suggestions...")

suggestions = get_ai_suggestions(description)

print("\nSuggestions:")
print(suggestions)

