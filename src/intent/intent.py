from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

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
            functions_info[name] = inspect.getdoc(obj)
    return functions_info
