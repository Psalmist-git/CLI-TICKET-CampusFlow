from ai_assistant import get_ticket_intelligence

description = """
The Wi-Fi connection in the library has stopped working.
Students cannot access the internet.
"""

result = get_ticket_intelligence(description)

print("\nCAMPUSFLOW AI INTELLIGENCE")
print("-------------------------")

if result:
    print("Category:", result["category"])
    print("Priority:", result["priority"])
    print("Department:", result["department"])
    print("Reason:", result["reason"])
else:
    print("AI intelligence is currently unavailable.")
