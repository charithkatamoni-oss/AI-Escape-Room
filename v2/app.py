"""Hale & Daughters — Version 2, Streamlit interface.

Run:  streamlit run v2/app.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from command_parser import looks_like_injection, parse
from engine import Game
from llm import LLM, classify, narrate

REFUSAL = "The Clockmaker only yawns. \"No shortcuts in this shop.\""

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hale & Daughters",
    page_icon="🕰️",
    layout="centered",
)

st.title("🕰️ Hale & Daughters")
st.caption("A text escape room — Version 2")

# ── session state ─────────────────────────────────────────────────────────────
if "game" not in st.session_state:
    st.session_state.game = Game()
    st.session_state.llm = LLM()
    intro = st.session_state.game.intro()
    narrated, _ = narrate(st.session_state.llm, intro)
    st.session_state.history = [("🎭", narrated)]
    st.session_state.won = False

game: Game = st.session_state.game
llm: LLM = st.session_state.llm

# ── restart button ────────────────────────────────────────────────────────────
if st.button("🔄 Restart game"):
    del st.session_state["game"]
    del st.session_state["llm"]
    del st.session_state["history"]
    del st.session_state["won"]
    st.rerun()

# ── chat history ──────────────────────────────────────────────────────────────
for role, msg in st.session_state.history:
    if role == "🎭":
        with st.chat_message("assistant", avatar="🎭"):
            st.write(msg)
    else:
        with st.chat_message("user", avatar="🧑"):
            st.write(msg)

# ── win state ─────────────────────────────────────────────────────────────────
if st.session_state.won:
    st.success(f"🎉 You escaped in **{game.state.moves}** moves using **{game.state.hints_used}** hints!")
    st.stop()

# ── input ─────────────────────────────────────────────────────────────────────
st.markdown("**Commands:** look · examine · take · use X on Y · enter CODE · inventory · hint · quit")

user_input = st.chat_input("What do you do?")

if user_input:
    text = user_input.strip()
    st.session_state.history.append(("🧑", text))

    if text.lower() in ("quit", "exit", "q"):
        reply = "You choose to stay. The cellar door remains closed."
    elif looks_like_injection(text):
        reply = REFUSAL
    else:
        action = parse(text)
        if action["action"] == "unknown" and llm.online:
            action = classify(llm, text)
        facts = game.handle(action)
        narrated, ok = narrate(llm, facts)
        reply = narrated
        if llm.online and not ok:
            reply += "\n\n*(narrator unavailable — plain text)*"

    st.session_state.history.append(("🎭", reply))

    if game.won:
        st.session_state.won = True

    st.rerun()