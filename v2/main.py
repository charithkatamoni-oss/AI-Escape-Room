"""Hale & Daughters, Version 2.

The engine decides what is true. The model only describes it.

Run:          python v2/main.py
No internet:  python v2/main.py --offline
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_parser import looks_like_injection, parse
from engine import Game
from llm import LLM, classify, narrate

REFUSAL = "The Clockmaker only yawns. \"No shortcuts in this shop.\""


def show(llm, facts):
    text, ok = narrate(llm, facts)
    print("\n" + text)
    if llm.online and not ok:
        print("(narrator unavailable, showing plain text)")


def main():
    offline = "--offline" in sys.argv
    llm = LLM(offline=offline)
    game = Game()

    print("=== HALE & DAUGHTERS (Version 2) ===")
    print("Type 'quit' to leave.")
    if not llm.online:
        print("(running without the narrator: plain text mode)")
    show(llm, game.intro())

    while not game.won:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if text.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            return
        if not text:
            continue
        if looks_like_injection(text):
            print("\n" + REFUSAL)
            continue

        action = parse(text)
        if action["action"] == "unknown" and llm.online:
            action = classify(llm, text)
        show(llm, game.handle(action))

    print(f"\nYou escaped in {game.state.moves} moves, using {game.state.hints_used} hints.")


if __name__ == "__main__":
    main()