"""Turns free text into a structured action, without any language model.

Version 2 keeps the model out of the rules. This rule-based parser handles
the normal commands. Only when it gives up does main.py ask the model to
classify the sentence (and even then the answer is validated).
"""
import re

from engine import ALIASES

_ALIAS_LIST = sorted(
    ((word, key) for key, words in ALIASES.items() for word in words),
    key=lambda pair: -len(pair[0]),
)

INJECTION_PATTERNS = [
    r"ignore (all |any |your )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"system prompt",
    r"repeat (everything|all|the text|your instructions)",
    r"(developer|debug|admin|god) mode",
    r"you are now",
    r"pretend (to be|you are)",
    r"reveal (your|the) (instructions|prompt|rules|solution|answer)",
    r"\bsolution\b|\bwalkthrough\b|\bcheat",
]


def normalize(text):
    t = text.lower().replace("'", "")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def looks_like_injection(text):
    t = normalize(text)
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


def find_thing(fragment):
    """Return the key of the first known thing named in the fragment."""
    for word, key in _ALIAS_LIST:
        if re.search(rf"\b{re.escape(word)}\b", fragment):
            return key
    return None


def _after(verb_pattern, t):
    m = re.search(verb_pattern, t)
    return t[m.end():] if m else t


def parse(text):
    """Return {"action": ..., "thing": ..., "tool": ..., "code": ...}."""
    t = normalize(text)
    if not t:
        return {"action": "unknown"}

    code_match = re.search(r"\b(\d{4})\b", t)
    code = code_match.group(1) if code_match else None

    # entering a code
    if code and (
        t == code
        or re.search(r"\b(enter|dial|type|try|input|set|punch|combination|code|unlock)\b", t)
        or find_thing(t) == "drawer"
    ):
        return {"action": "enter_code", "code": code}

    # asking for the code
    if not code and re.search(r"\b(code|combination|password|passcode|pin)\b", t):
        return {"action": "ask_code"}

    # inventory
    if re.search(r"\b(inventory|inv)\b", t) or re.search(r"\bwhat (do|am) i (have|carrying|holding)\b", t):
        return {"action": "inventory"}

    # hint
    if re.search(r"\b(hint|clue|stuck)\b", t) or "help me" in t:
        return {"action": "hint"}

    # winding the music box
    if re.search(r"\bwind\b", t):
        return {"action": "use", "tool": "winding_key", "thing": "music_box"}

    # use X on Y
    m = re.search(
        r"\b(use|insert|put|place|apply|try|unlock|open)\s+(.+?)\s+(on|with|in|into|to|at)\s+(.+)$", t
    )
    if m:
        verb, first, second = m.group(1), m.group(2), m.group(4)
        if verb in ("unlock", "open"):
            target, tool = find_thing(first), find_thing(second)
        else:
            tool, target = find_thing(first), find_thing(second)
        return {"action": "use", "tool": tool, "thing": target}

    # use X (no target)
    m = re.search(r"\b(use|insert|apply)\s+(.+)$", t)
    if m:
        return {"action": "use", "tool": find_thing(m.group(2)), "thing": None}

    # take X
    if re.search(r"\b(take|grab|get|collect|fetch|pick up|pick|steal)\b", t):
        rest = _after(r"\b(take|grab|get|collect|fetch|pick up|pick|steal)\b", t)
        rest = re.split(r"\b(from|out of|off|inside|in)\b", rest)[0]
        return {"action": "take", "thing": find_thing(rest)}

    # open / unlock X
    if re.search(r"\b(open|unlock)\b", t):
        rest = _after(r"\b(open|unlock)\b", t)
        return {"action": "open", "thing": find_thing(rest)}

    # examine X
    if re.search(
        r"\b(examine|inspect|check|read|study|search|investigate|describe|peek|"
        r"look at|look in|look inside|look under|look closely)\b", t
    ):
        return {"action": "examine", "thing": find_thing(t)}

    # look
    if re.search(r"\b(look|where am i|surroundings)\b", t):
        thing = find_thing(t)
        if thing:
            return {"action": "examine", "thing": thing}
        return {"action": "look"}

    return {"action": "unknown"}