from enum import Enum


class TrackState(Enum):
    EMPTY = "EMPTY"
    RESERVED = "RESERVED"
    DELIVERING = "DELIVERING"
    FULL = "FULL"
    CONSUMING = "CONSUMING"
    RETURN_PENDING = "RETURN_PENDING"
    BLOCKED = "BLOCKED"

    @classmethod
    def names(cls):
        return [s.value for s in cls]
