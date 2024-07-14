from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    examples: list[str] | None = None
    description: str | None = None

    def __eq__(self, other: Intent) -> bool:
        if isinstance(other, Intent):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)


CALENDAR: Intent = Intent(
    name="Calendar",
    examples=[
        "Create an event",
        "Schedule a meeting",
        "What's my next event?",
    ],
    description="Manages calendar-related activities such as creating, deleting, or listing events and tasks, "
    "and answering schedule-related questions.",
)

LECTURE: Intent = Intent(
    name="Lecture",
    examples=[
        "Translate the lecture notes",
        "Convert the lecture audio to text",
        "What's the lecture summary?",
    ],
    description="Handles tasks related to lectures, including translating notes, transcribing audio, summarizing "
    "content, and creating study aids like Anki cards.",
)

CHAT_HISTORY: Intent = Intent(
    name="ChatHistory",
    examples=[
        "What was the name of the first function that we've called?",
        "At what time the last appointment we've created start?",
        "What was the name of the first meeting we have scheduled?",
    ],
    description="Handles tasks related to chat history. This includes any questions about previous interactions, such as details of appointments (e.g., names, times, duration, and order), the number of times specific actions were taken (e.g., creating or deleting appointments, asking about lecture content), and other historical queries regarding the chat's activity.",
)

UNKNOWN: Intent = Intent(
    name="Unknown",
    examples=[
        "Blorf zibber zquark",
        "Let's throw a stone at moond",
        "Who won the last football match?",
    ],
    description="Handles activities that do not fit into any predefined classes.",
)
