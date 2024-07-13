from __future__ import annotations

import enum
import json
from dataclasses import asdict, dataclass

from src.classifier.base_classifier import ClassifierResponse


class Role(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    text: str | None = None
    role: Role | None = None
    function_call: str | None = None
    function_args: dict | None = None
    function_response: dict | None = None
    is_slot_filling: bool = False
    classifier_response_level_0: ClassifierResponse | None = None
    classifier_response_level_1: ClassifierResponse | None = None
    llm_full_output_slot_filler: str | None = None
    is_custom_response: bool = False

    def set_text(self, text):
        self.text = text
        return self

    def set_role(self, role: Role):
        self.role = role
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

    def set_classifier_response_level_0(self, full_output: str):
        self.classifier_response_level_0 = full_output
        return self

    def set_classifier_response_level_1(self, full_output: str):
        self.classifier_response_level_1 = full_output
        return self

    def set_llm_full_output_slot_filler(self, full_output: str):
        self.llm_full_output_slot_filler = full_output
        return self

    def set_is_custom_response(self, *, is_custom_response: bool):
        self.is_custom_response = is_custom_response

    def __str__(self):
        data = {
            k: (v.value if isinstance(v, Role) else v)
            for k, v in asdict(self).items()
            if v is not None and k in ["text", "role"]
        }
        return json.dumps(data, indent=4)


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

    def get_chat_template_messages(self, last_n: int = 0):
        messages = [{"role": msg.role.value, "message": msg.text} for msg in self if not msg.is_slot_filling]
        return messages[last_n:]

    def get_annotated_history(self, last_n: int  = 0):
        messages = [f"{msg.role.value}: {msg.text}" for msg in self]
        return "\n".join(messages[last_n:])

    def clear_history(self):
        self.conversation = []

    def get_latest_highest_level_llm_output(self) -> str | None:
        for msg in reversed(self.conversation):
            if msg.role == Role.USER:
                if msg.classifier_response_level_1 is not None:
                    return msg.classifier_response_level_1.llm_response
                if msg.classifier_response_level_0 is not None:
                    return msg.classifier_response_level_0
        return None

    def set_llm_full_output_level_0(self, classifier_response: ClassifierResponse):
        for msg in reversed(self.conversation):
            if msg.role == Role.USER:
                msg.classifier_response_level_0 = classifier_response
                break

    def set_classifier_response_level_1(self, classifier_response: ClassifierResponse):
        for msg in reversed(self.conversation):
            if msg.role == Role.USER:
                msg.classifier_response_level_1 = classifier_response
                break

    def set_llm_full_output_slot_filler(self, full_output: str):
        for msg in reversed(self.conversation):
            if msg.role == Role.USER:
                msg.llm_full_output_slot_filler = full_output
                break

    def __iter__(self):
        return iter(self.conversation)

    def __str__(self) -> str:
        return json.dumps(
            [
                {
                    "text": msg.text,
                    "role": msg.role.value,
                    "function_call": msg.function_call,
                }
                for msg in self.conversation
                if msg.text and msg.role
            ],
            indent=2,
        )

    def get_level_1_history(self, last_n: int | None = None) -> list[dict]:
        messages = []
        for msg in self:
            if msg.classifier_response_level_1 is not None:
                messages.append({"role": msg.role.value, "content": msg.text})
                messages.append({"role": Role.ASSISTANT.value, "content": msg.classifier_response_level_1.llm_response})
        if last_n:
            return messages[last_n:]
        return messages
