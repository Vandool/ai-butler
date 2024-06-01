from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Final

from src.intent.processable import Processable


@dataclass
class Intent:
    name: str
    intent_processor: Processable | None = None
    examples: list[str] | None = None
    description: str | None = None

    def __eq__(self, other: Intent) -> bool:
        if isinstance(other, Intent):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)


_IS_MARKED_ATTR: Final[str] = "_is_marked"


def mark_intent(func: Callable) -> Callable:
    setattr(func, _IS_MARKED_ATTR, True)
    return func


def get_marked_functions_and_docstrings(module) -> dict[str, str]:
    functions_info = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and getattr(obj, _IS_MARKED_ATTR, False):
            requires_params = bool(inspect.signature(obj).parameters)
            functions_info[name] = (inspect.getdoc(obj), {"requires_params": requires_params})
    return functions_info


@dataclass
class Slot:
    name: str
    param_type: type
    is_required: bool
    # Idea: based on the attempts made we can modify the prompt to ask more specific question
    attempts: int = 0
    value: Any = None
    is_set: bool = field(default=False, init=False)

    def set_value(self, value: Any):
        # TODO(Arvand): Here we neeed type checking, we need a proper setter, maybe using llm
        self.value = value
        self.is_set = True
        self.attempts += 1

    def get_name_value(self):
        return {"name": self.name, "value": self.value}

    def __str__(self):
        return str(json.dumps(self.__dict__, indent=2))


def extract_slots_from_function(func) -> list[Slot]:
    sig = inspect.signature(func)
    slots = []
    for param in sig.parameters.values():
        required = param.default is param.empty
        slots.append(Slot(param.name, param.annotation, required))
    return slots
