from enum import Enum


class VoiceState(str, Enum):
    IDLE = "IDLE"
    PREPARING = "PREPARING"
    SPEAKING = "SPEAKING"
    STOPPING = "STOPPING"
    ERROR = "ERROR"
