from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from transformers import pipeline

from src.classifier.base_classifier import BaseClassifier
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptType


@dataclass
class ZeroShotClassifierResponse:
    labels: list[str]
    scores: list[float]
    sequence: str

    def get_best_label(self) -> str:
        return self.labels[np.argmax(self.scores)]


class ZeroShotClassifier(BaseClassifier):
    def __init__(self, model: str, intent_manager: IntentManager | None = None):
        super().__init__()
        self._classifier = pipeline(self.name, model=model)
        self.intent_manager = intent_manager

    @property
    def name(self) -> str:
        return "zero-shot-classification"

    def classify_with_details(
        self,
        input_text: str,
        _: PromptType = PromptType.ZERO_SHOT,
    ) -> ZeroShotClassifierResponse:
        response = ZeroShotClassifierResponse(**self._classifier(input_text, self.intent_manager.list_intent_names()))
        self.logger.debug("%s detailed response:\n%s", self.name, response)
        return response

    def classify(self, input_text: str, _: str = "simple") -> str:
        return self.classify_with_details(input_text=input_text).get_best_label()
