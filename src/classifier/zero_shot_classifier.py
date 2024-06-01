from dataclasses import dataclass

import numpy as np
from transformers import pipeline

from src.classifier.base_classifier import BaseIntentClassifier


@dataclass
class ZeroShotClassifierResponse:
    labels: list[str]
    scores: list[float]
    sequence: "str"

    def get_best_label(self) -> str:
        return self.labels[np.argmax(self.scores)]


class ZeroShotClassifier(BaseIntentClassifier):
    def __init__(self, model: str, num_shots: int = 0):
        super().__init__(num_shots)
        self.classifier = pipeline(self.name, model=model)

    @property
    def name(self) -> str:
        return "zero-shot-classification"

    def classify_with_details(self, input_text: str, _: str = "simple") -> ZeroShotClassifierResponse:
        response = ZeroShotClassifierResponse(**self.classifier(input_text, self.intent_manager.list_intent_names()))
        self.logger.debug("%s detailed response:\n%s", self.name, response)
        return response

    def classify(self, input_text: str, _: str = "simple") -> str:
        return self.classify_with_details(input_text=input_text).get_best_label()
