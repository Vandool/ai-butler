from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HistoryEntry:
    user: str | None = None
    ai_assistant: str | None = None
    intent_name: str | None = None
    function_call: str | None = None
    function_args: dict | None = None
    function_response: dict | None = None
    current_state: str | None = None
    previous_state: str | None = None

    def set_user(self, user):
        self.user = user
        return self

    def set_ai_assistant(self, ai_assistant: str):
        self.ai_assistant = ai_assistant
        return self

    def set_intent_name(self, intent_name: str):
        self.intent_name = intent_name
        return self

    def set_function_call(self, function_call: str):
        self.function_call = function_call
        return self

    def set_function_args(self, function_args: dict):
        self.function_args = function_args
        return self

    def set_function_response(self, function_response: dict):
        self.function_response = function_response
        return self

    def set_current(self, state_name: str):
        self.current_state = state_name
        return self

    def set_previous_state(self, previous_state: str):
        self.previous_state = previous_state
        return self


class History:
    def __init__(self):
        self.conversation: list[HistoryEntry] = []

    @property
    def is_empty(self):
        return len(self.conversation) == 0

    def add_entry(self, entry: HistoryEntry):
        self.conversation.append(entry)

    def add_history(self, history: History):
        self.conversation.extend(history.conversation)

    def get_chat_history(self, user_alias: str | None, bot_alias: str | None) -> str:
        """Get the chat history which always starts with user."""
        history_str = ""
        for entry in self.conversation:
            history_str += f"{entry['role']}: {entry['message']}\n"
        return history_str

    def clear_history(self):
        self.conversation = []

    def __str__(self):
        return self.get_history()

    def __iter__(self):
        return iter(self.conversation)


if __name__ == "__main__":
    history = History()
    history.add_human_message("I want to create an appointment.")
    history.add_ai_message("Please provide the summary of the appointment.")
    print(history)
    history.add_history(history)
    print(history)
    history.clear_history()

    entry = HistoryEntry()
    entry.set_ai_assistant("<NAME>").set_intent_name("name")
    print(entry)
