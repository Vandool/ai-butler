from __future__ import annotations

from src.classifier.base_classifier import BaseClassifier
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient
from src.prompt_generator.prompt_generator import PromptType

MAX_NEW_TOKENS = 128


class FewShotTextGenerationClassifier(BaseClassifier):
    def __init__(self, llm_client: LLMClient, intent_manager: IntentManager | None = None):
        super().__init__()
        self.llm_client = llm_client
        self.intent_manager = intent_manager

    @property
    def name(self) -> str:
        return "few_shot_text_generation_classifier"

    def _get_llm_response(self, input_text: str, prompt_type: PromptType) -> str:
        generated_text = self.llm_client.get_response(
            prompt=self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type),
            max_new_tokens=MAX_NEW_TOKENS,
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text
