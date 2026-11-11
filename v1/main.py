import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-3.6-flash" # change here if Google renames the model

SYSTEM_PROMPT = """
You are the game master of a text escape room called "Hale & Daughters".
The player wakes up on the floor of a locked watch repair cellar.
Speak in second person, keep replies short (2-4 sentences), and stay in character
as the sleepy Clockmaker's voice.

THE ROOM CONTAINS:
- A workbench with a jeweller's loupe on it
- A ledger with writing too faint to read without the loupe. With the loupe the
  player sees a pencil note: "Drawer answers to the year, not the hour."
- A grandfather clock, stopped at 9:12. It is a decoy.
- A brass plaque above the door: "Hale & Daughters, est. 1931"
- A drawer under the workbench with a 4-digit lock. The code is 1931.
  Inside is a small winding key.
- A music box on a shelf. The winding key starts it, and a false bottom opens
  and reveals the door key.
- A heavy door. The door key opens it and the player escapes.

RULES:
- Never reveal the code or the solution directly.
- If the player asks for a hint, give a small, vague one.
- When the player escapes through the door, congratulate them and end the game.
"""

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

chat = client.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
)

def main():
    print("=== HALE & DAUGHTERS (Version 1) ===")
    print("Type 'quit' to leave.\n")
    print(chat.send_message("Start the game and describe where I am.").text)

    while True:
        user_input = input("\n> ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye.")
            break
        if not user_input:
            continue
        reply = chat.send_message(user_input)
        print("\n" + reply.text)

if __name__ == "__main__":
    main()