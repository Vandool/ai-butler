from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Intent:
    name: str
    examples: list[str]
    description: str | None = None
