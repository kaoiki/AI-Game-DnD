from enum import Enum

class EventType(str, Enum):
    INIT = "init"
    DECISION = "decision"
    COMBAT = "combat"
    PUZZLE = "puzzle"
    END = "end"
    NOVEL = "novel"

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in cls._value2member_map_