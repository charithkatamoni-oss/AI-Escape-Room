"""Game engine for Hale & Daughters (Version 2).

The engine is the single source of truth. It knows the secrets, tracks the
state and decides what is true. The language model never decides anything:
it only receives the facts this file produces and rewords them.
"""
from dataclasses import dataclass, field

# --- secrets: these live only in code, never in a prompt -------------------
DRAWER_CODE = "1931"

# --- the world --------------------------------------------------------------
ITEM_LABELS = {
    "loupe": "jeweller's loupe",
    "winding_key": "winding key",
    "door_key": "door key",
}
OBJECTS = ("workbench", "ledger", "clock", "plaque", "drawer", "music_box", "door")

# words a player may use for each thing (used by command_parser.py)
ALIASES = {
    "workbench": ["workbench", "work bench", "bench", "desk", "table"],
    "ledger": ["ledger", "book", "notebook", "logbook"],
    "clock": ["grandfather clock", "clock"],
    "plaque": ["brass plaque", "plaque", "sign"],
    "drawer": ["drawer"],
    "music_box": ["music box", "musicbox", "box"],
    "door": ["door", "exit"],
    "loupe": ["jewellers loupe", "jewelers loupe", "magnifying glass",
              "magnifier", "loupe", "lens"],
    "winding_key": ["winding key", "small key", "brass key"],
    "door_key": ["door key", "iron key", "heavy key"],
    "key": ["key"],  # ambiguous, resolved by the engine from context
}


@dataclass
class GameState:
    inventory: list = field(default_factory=list)
    ledger_read: bool = False
    drawer_open: bool = False
    music_box_open: bool = False
    door_open: bool = False
    moves: int = 0
    hints_used: int = 0


class Game:
    def __init__(self):
        self.state = GameState()

    @property
    def won(self):
        return self.state.door_open

    # ------------------------------------------------------------------ intro
    def intro(self):
        return ("You wake on the floor of a locked watch repair cellar. "
                "A cluttered workbench, a grandfather clock, a ledger, a music "
                "box on a shelf and a heavy door surround you.")

    # --------------------------------------------------------------- dispatch
    def handle(self, action):
        """Take a structured action, update the state, return plain facts."""
        kind = action.get("action", "unknown")
        thing = action.get("thing")
        tool = action.get("tool")
        code = action.get("code")

        if kind == "unknown":
            return "That is not something you can do here."

        self.state.moves += 1

        if kind == "look":
            return self._look()
        if kind == "examine":
            return self._examine(thing)
        if kind == "take":
            return self._take(thing)
        if kind == "use":
            return self._use(tool, thing)
        if kind == "open":
            return self._open(thing)
        if kind == "enter_code":
            return self._enter_code(code)
        if kind == "ask_code":
            return ("Nobody will simply tell you the combination. "
                    "The answer has to be found in this room.")
        if kind == "inventory":
            return self._inventory()
        if kind == "hint":
            return self._hint()
        return "That is not something you can do here."

    # ---------------------------------------------------------------- helpers
    def _has(self, item):
        return item in self.state.inventory

    def _resolve_key(self, thing, target=None, mode="take"):
        """Turn the vague word 'key' into winding_key or door_key."""
        if thing != "key":
            return thing
        s = self.state
        if target == "music_box":
            return "winding_key"
        if target == "door":
            return "door_key"
        if mode == "take":
            if s.drawer_open and not self._has("winding_key"):
                return "winding_key"
            if s.music_box_open and not self._has("door_key"):
                return "door_key"
            return None
        held = [k for k in ("winding_key", "door_key") if self._has(k)]
        if len(held) == 1:
            return held[0]
        return None

    # ------------------------------------------------------------------- look
    def _look(self):
        s = self.state
        parts = ["You are in a cramped cellar under a watch repair shop. "
                 "You can see a workbench, a ledger, a grandfather clock, "
                 "a brass plaque above the heavy door, a drawer under the "
                 "workbench, and a music box on a shelf."]
        if not self._has("loupe"):
            parts.append("Something small and shiny lies among the clutter on the workbench.")
        return " ".join(parts)

    # ---------------------------------------------------------------- examine
    def _examine(self, thing):
        s = self.state
        if thing is None:
            return self._look()
        thing = self._resolve_key(thing, mode="examine")
        if thing is None:
            return "Which key do you mean?"

        if thing == "workbench":
            if not self._has("loupe"):
                return ("The workbench is covered in oily tools and tiny screws. "
                        "A brass-rimmed jeweller's loupe lies among them.")
            return "The workbench holds only oily tools and tiny screws."
        if thing == "ledger":
            if s.ledger_read:
                return ('Through the loupe a faint pencil note appears in the ledger: '
                        '"Drawer answers to the year, not the hour."')
            return ("The ledger is an old customer book. The handwriting is too "
                    "faint to read with the naked eye.")
        if thing == "clock":
            return "The grandfather clock has stopped. Its hands show 9:12."
        if thing == "plaque":
            return 'The brass plaque above the door reads: "Hale & Daughters, est. 1931".'
        if thing == "drawer":
            if not s.drawer_open:
                return "The drawer under the workbench is locked with a four-digit dial."
            if self._has("winding_key"):
                return "The drawer is open and empty."
            return "The drawer is open. A small winding key lies inside."
        if thing == "music_box":
            if not s.music_box_open:
                return "A small wooden music box with a keyhole in its side. It is silent."
            if self._has("door_key"):
                return "The music box is open. Its false bottom is empty."
            return "The music box is open. A heavy door key lies in its false bottom."
        if thing == "door":
            return "The heavy door is locked with a brass lock."
        if thing == "loupe":
            if self._has("loupe"):
                return "A brass-rimmed jeweller's loupe. It makes small things large."
            return "A brass-rimmed jeweller's loupe lies on the workbench."
        if thing == "winding_key":
            if self._has("winding_key"):
                return "A small brass winding key."
            if s.drawer_open:
                return "A small winding key lies in the open drawer."
            return "You don't see that here."
        if thing == "door_key":
            if self._has("door_key"):
                return "A heavy iron door key."
            if s.music_box_open:
                return "A heavy door key lies in the music box."
            return "You don't see that here."
        return "You don't see that here."

    # ------------------------------------------------------------------- take
    def _take(self, thing):
        s = self.state
        if thing is None:
            return "Take what?"
        thing = self._resolve_key(thing, mode="take")
        if thing is None:
            return "You don't see a key within reach."
        if thing not in ITEM_LABELS:
            return "You can't pick that up."
        label = ITEM_LABELS[thing]
        if self._has(thing):
            return f"You already have the {label}."

        if thing == "loupe":
            s.inventory.append("loupe")
            return "You pick up the jeweller's loupe from the workbench."
        if thing == "winding_key":
            if not s.drawer_open:
                return "You don't see a winding key within reach."
            s.inventory.append("winding_key")
            return "You take the winding key from the open drawer."
        if thing == "door_key":
            if not s.music_box_open:
                return "You don't see a door key within reach."
            s.inventory.append("door_key")
            return "You take the door key from the music box."
        return "You don't see that here."

    # -------------------------------------------------------------------- use
    def _use(self, tool, target):
        s = self.state
        if tool is None:
            return "Use what?"
        tool = self._resolve_key(tool, target=target, mode="use")
        if tool is None:
            return "Which key do you mean?"
        if tool not in ITEM_LABELS:
            return "You can't use that."
        label = ITEM_LABELS[tool]
        if not self._has(tool):
            return f"You are not carrying a {label}."
        if target is None:
            return f"Use the {label} on what?"

        if tool == "loupe":
            if target == "ledger":
                if s.ledger_read:
                    return ('You study the ledger again. The faint pencil note still '
                            'reads: "Drawer answers to the year, not the hour."')
                s.ledger_read = True
                return ('Through the loupe a faint pencil note appears in the ledger: '
                        '"Drawer answers to the year, not the hour."')
            return "You look through the loupe, but find nothing new."

        if tool == "winding_key":
            if target == "music_box":
                if s.music_box_open:
                    return "The music box is already open."
                s.music_box_open = True
                return ("You wind the music box with the winding key. It plays a few "
                        "bars and a false bottom pops open. A heavy door key lies inside.")
            if target == "drawer":
                return "The winding key does not fit. The drawer takes a four-digit code."
            return "Nothing happens."

        if tool == "door_key":
            if target == "door":
                s.door_open = True
                return ("The door key turns in the brass lock and the heavy door swings "
                        f"open. You escaped in {s.moves} moves, using {s.hints_used} hints.")
            return "Nothing happens."

        return "Nothing happens."

    # ------------------------------------------------------------------- open
    def _open(self, thing):
        s = self.state
        if thing is None:
            return "Open what?"
        if thing == "door":
            if self._has("door_key"):
                return self._use("door_key", "door")
            return "The door is locked. You need a key."
        if thing == "drawer":
            if s.drawer_open:
                return "The drawer is already open."
            return "The drawer is locked with a four-digit dial."
        if thing == "music_box":
            if s.music_box_open:
                return "The music box is already open."
            return "The music box is shut. It has a keyhole in its side."
        if thing == "ledger":
            return self._examine("ledger")
        return "That does not open."

    # ------------------------------------------------------------- enter code
    def _enter_code(self, code):
        s = self.state
        if s.drawer_open:
            return "The drawer is already open."
        if not code:
            return "The drawer needs a four-digit code."
        if code == DRAWER_CODE:
            s.drawer_open = True
            return ("You dial the code into the drawer. The lock clicks and the drawer "
                    "slides open. A small winding key lies inside.")
        return "You dial the code, but the drawer stays shut."

    # -------------------------------------------------------------- inventory
    def _inventory(self):
        inv = self.state.inventory
        if not inv:
            return "You are carrying nothing."
        names = [ITEM_LABELS[i] for i in inv]
        return "You are carrying: " + ", ".join(names) + "."

    # ------------------------------------------------------------------- hint
    def _hint(self):
        s = self.state
        s.hints_used += 1
        if not self._has("loupe"):
            return "Hint: not everything on the workbench is junk."
        if not s.ledger_read:
            return "Hint: some writing can only be read up close."
        if not s.drawer_open:
            return "Hint: the clock is lying to you. Look at the door instead."
        if not self._has("winding_key"):
            return "Hint: the drawer is open. Something inside is worth taking."
        if not s.music_box_open:
            return "Hint: a key made for winding belongs in something that plays."
        if not self._has("door_key"):
            return "Hint: the music box is hiding something."
        return "Hint: you hold everything you need. Try the door."