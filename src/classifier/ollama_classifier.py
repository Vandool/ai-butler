from typing import Any

import ollama

from src.classifier.base_classifier import BaseClassifier
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptType

MAX_NEW_TOKENS = 128
OLLAMA_MODEL = 'llama3'


class OllamaClassifier(BaseClassifier):
    def __init__(self, intent_manager: IntentManager | None = None):
        super().__init__()
        self.intent_manager = intent_manager

    @property
    def name(self) -> str:
        return "ollama_classifier"

    def _get_llm_response(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
        prompt = self._prompt_generator.generate_prompt(input_text, prompt_type=prompt_type)
        print(prompt)
        return ollama.generate(prompt=prompt, model=OLLAMA_MODEL)['response']
