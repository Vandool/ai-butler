from __future__ import annotations

import json
from typing import Any

from huggingface_hub import InferenceClient

from src.classifier.base_classifier import BaseClassifier
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptType


class FewShotTextGenerationClassifier(BaseClassifier):
    def __init__(self, llm_url: str, intent_manager: IntentManager | None = None):
        super().__init__()
        self.client = InferenceClient(model=llm_url)
        self.intent_manager = intent_manager

    @property
    def name(self) -> str:
        return "few_shot_text_generation_classifier"

    def classify(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
        generated_text = self.client.text_generation(
            prompt=self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type),
            max_new_tokens=self.intent_manager.get_max_name_length(),
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text

    def classify_with_details(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> Any:
        response = self.client.text_generation(
            prompt=self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type),
            details=True,
            max_new_tokens=self.intent_manager.get_max_name_length(),
        )
        self.logger.debug("Client Response Details:\n%s", json.dumps(vars(response), indent=2))
        return response

    def get_closest_intent(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> Intent:
        return self.intent_manager.get_closest_intent(
            message=self.classify(input_text, prompt_type),
        )
