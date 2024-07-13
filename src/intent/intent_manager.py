from __future__ import annotations

from collections.abc import Iterator

from src import intent, utils
from src.intent import intent


# Design Decision: How to classify hierarchical classes?


class IntentManager:
    def __init__(self):
        self._intents: list[intent.Intent] = []
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
                self.add_intent(intent.UNKNOWN)
            else:
                self._intents = [i for i in self if i.name != "Unknown"]

    def get_intent_length(self) -> int:
        return len(self._intents)

    def get_max_name_length(self) -> int:
        return max([len(i.name) for i in self])

    def add_intent(self, the_intent: intent.Intent) -> None:
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

    def get_closest_intent_simple(self, message: str) -> intent.Intent | None:
        message_lower = message.lower()
        for intent_ in self:
            if intent_.name.lower() in message_lower:
                return intent_

        if self.use_unknown_intent:
            return intent.UNKNOWN
        return None

    def __iter__(self) -> Iterator[intent.Intent]:
        """Return an iterator over the intents."""
        return iter(self._intents)

    def __str__(self) -> str:
        """Return a string representation of all intents."""
        return "\n".join(f"{i.name}: {i.description}" for i in self)


class IntentManagerFactory:
    @staticmethod
    def get_intent_manager_with_unknown_intent() -> IntentManager:
        intent_manager = IntentManager()
        intent_manager.add_intent(intent.CALENDAR)
        intent_manager.add_intent(intent.LECTURE)
        intent_manager.add_intent(intent.CHAT_HISTORY)
        intent_manager.use_unknown_intent = True
        return intent_manager


if __name__ == "__main__":
    manager = IntentManager()

    # Adding intents
    manager.add_intent(intent.CALENDAR)
    manager.add_intent(intent.LECTURE)

    print(manager.list_intent_names())

    print(manager.get_all_examples(num_shots=1))

    for intent in manager:
        print(f"Name: {intent.name}, Description: {intent.description}")
    print(manager.get_intent_length())
    print(manager.get_max_name_length())

    print(manager)
