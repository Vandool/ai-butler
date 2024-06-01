import json
from typing import Any

from huggingface_hub import InferenceClient

from src.classifier.base_classifier import BaseIntentClassifier
from src.intent.intent import Intent


class FewShotTextGenerationClassifier(BaseIntentClassifier):
    def __init__(self, llm_url: str, num_shots: int = 1):
        super().__init__(num_shots)
        self.client = InferenceClient(model=llm_url)

    @property
    def name(self) -> str:
        return "few_shot_text_generation_classifier"

    def classify(self, input_text: str, prompt_type: str = "simple") -> str:
        generated_text = self.client.text_generation(
            prompt=self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type),
            max_new_tokens=self.intent_manager.get_max_name_length(),
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text

    def classify_with_details(self, input_text: str, prompt_type: str = "simple") -> Any:
        response = self.client.text_generation(
            prompt=self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type),
            details=True,
            max_new_tokens=self.intent_manager.get_max_name_length(),
        )
        self.logger.debug("Client Response Details:\n%s", json.dumps(vars(response), indent=2))
        return response

    def get_closest_intent(self, input_text: str, prompt_type: str = "simple") -> Intent:
        return self.intent_manager.get_closest_intent(
            message=self.classify(input_text, prompt_type),
        )
