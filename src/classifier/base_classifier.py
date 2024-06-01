from __future__ import annotations

import abc

from src import utils
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptGenerator


class BaseIntentClassifier(abc.ABC):
    def __init__(self, num_shots: int = 0):
        self.logger = utils.get_logger(self.__class__.__name__)
        self._intent_manager: IntentManager | None = None
        self._prompt_generator: PromptGenerator | None = None
        self._num_shots: int = num_shots

    @abc.abstractmethod
    def classify(self, input_text: str, prompt_type: str = "simple") -> str:
        pass

    @abc.abstractmethod
    def classify_with_details(self, input_text: str, prompt_type: str = "simple") -> str:
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    def intent_manager(self) -> IntentManager | None:
        return self._intent_manager

    def get_closest_intent(self, input_text: str, prompt_type: str = "simple") -> Intent:
        return self.intent_manager.get_closest_intent(
            message=self.classify(input_text, prompt_type),
        )

    @intent_manager.setter
    def intent_manager(self, intent_manager: IntentManager) -> None:
        assert intent_manager.get_intent_length() > 1
        self._intent_manager = intent_manager
        self.__initialize_prompt_generator()

    def __initialize_prompt_generator(self):
        if self._intent_manager is not None:
            self._prompt_generator = PromptGenerator(intent_manager=self._intent_manager, num_shots=self._num_shots)
