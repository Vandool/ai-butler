from __future__ import annotations

import enum
from dataclasses import dataclass


class Role(enum.Enum):
    USER = "User"
    ASSISTANT = "Assistant"


@dataclass
class Message:
    text: str | None = None
    role: Role | None = None
    intent_name: str | None = None
    function_call: str | None = None
    function_args: dict | None = None
    function_response: dict | None = None
    current_state: str | None = None

    def set_text(self, text):
        self.text = text
        return self

    def set_role(self, role: Role):
        self.role = role
        return self

    def set_intent_name(self, name: str):
        self.intent_name = name
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

    def set_current_state(self, name: str):
        self.current_state = name
        return self


class ChatHistory:
    def __init__(self):
        self.conversation: list[Message] = []

    @property
    def is_empty(self):
        return len(self.conversation) == 0

    def add_message(self, msg: Message):
        self.conversation.append(msg)

    def add_history(self, history: ChatHistory):
        self.conversation.extend(history.conversation)

    def get_chat_template_message(self, last_n: int = 0):
        messages = [{"role": msg.role, "message": msg.text} for msg in self]
        return messages[last_n:]

    def get_annotated_history(self, last_n: int = 0):
        messages = [f"{msg.role.value}: {msg.text}" for msg in self]
        return "\n".join(messages[last_n:])

    def clear_history(self):
        self.conversation = []

    def __iter__(self):
        return iter(self.conversation)

    def __str__(self) -> str:
        return str([str(msg) for msg in self.conversation])


if __name__ == "__main__":
    history = ChatHistory()
    history.add_message(Message(text="Hi, do this", role=Role.USER).set_intent_name("Calendar"))
    history.add_message(Message(text="Oke", role=Role.ASSISTANT))

    print(history.get_chat_template_message())
    print(history.conversation)
