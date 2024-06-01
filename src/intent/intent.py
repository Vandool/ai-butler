from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    examples: list[str]
    description: str | None = None

    def __eq__(self, other: Intent) -> bool:
        if isinstance(other, Intent):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)
