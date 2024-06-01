from __future__ import annotations

from collections.abc import Iterator

import numpy as np
from sentence_transformers import SentenceTransformer

from src import utils
from src.intent.intent import Intent
from src.utils import calculate_similarity


class IntentManager:
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")

    def __init__(self):
        self._intents: list[Intent] = []
        self.logger = utils.get_logger(self.__class__.__name__)
        self._use_unknown_intent: bool = False

    @property
    def use_unknown_intent(self) -> bool:
        return self._use_unknown_intent

    @use_unknown_intent.setter
    def use_unknown_intent(self, value: bool) -> None:
        if self._use_unknown_intent != value:
            self._use_unknown_intent = value
            if value:
                self.add_intent(UNKNOWN)
            else:
                self._intents = [i for i in self if i.name != "Unknown"]

    def get_intent_length(self) -> int:
        return len(self._intents)

    def get_max_name_length(self) -> int:
        return max([len(i.name) for i in self])

    def add_intent(self, the_intent: Intent) -> None:
        """Add a new intent to the collection."""
        self._intents.append(the_intent)

    def list_intent_names(self) -> list[str]:
        """List all intent names."""
        return [i.name for i in self]

    def get_all_examples(self, num_shots: int) -> dict[str, list[str]]:
        """returns a dictionary of intent names and list of examples."""
        min_example = min([len(i.examples) for i in self])
        if num_shots > min_example:
            msg = "num_shots must be greater than min_examples given in IntentManager"
            raise ValueError(msg)

        return {i.name: i.examples[:num_shots] for i in self}

    def get_closest_intent(self, message: str):
        similarity_scores = [calculate_similarity(message, i.name) for i in self]
        self.logger.debug(f"Similarity scores: {list(zip(similarity_scores, self._intents, strict=False))}")
        return self._intents[np.argmax(similarity_scores)]

    def __iter__(self) -> Iterator[Intent]:
        """Return an iterator over the intents."""
        return iter(self._intents)

    def __str__(self) -> str:
        """Return a string representation of all intents."""
        return "\n".join(f"{i.name}: {i.description}" for i in self)


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

UNKNOWN: Intent = Intent(
    name="Unknown",
    examples=[
        "Blorf zibber zquark",
        "Let's throw a stone at moond",
        "Who won the last football match?",
    ],
    description="Handles activities that do not fit into any predefined classes.",
)

if __name__ == "__main__":
    manager = IntentManager()

    # Adding intents
    manager.add_intent(CALENDAR)
    manager.add_intent(LECTURE)

    print(manager.list_intent_names())

    print(manager.get_all_examples(num_shots=1))

    for intent in manager:
        print(f"Name: {intent.name}, Description: {intent.description}")
    print(manager.get_intent_length())
    print(manager.get_max_name_length())

    print(manager)
