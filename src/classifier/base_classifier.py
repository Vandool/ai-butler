from __future__ import annotations

import abc
from dataclasses import dataclass

from src import utils
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptGenerator, PromptType


@dataclass
class ClassifierResponse:
    intent: Intent
    llm_response: str | None = None


class BaseClassifier(abc.ABC):
    _PROMPT_TYPE: PromptType = PromptType.FEW_SHOT_DETAILED

    def __init__(self):
        self.logger = utils.get_logger(self.__class__.__name__)
        self._intent_manager: IntentManager | None = None
        self._prompt_generator: PromptGenerator | None = None

    @classmethod
    def set_prompt_type(cls, prompt_type: PromptType) -> None:
        cls._PROMPT_TYPE = prompt_type

    @abc.abstractmethod
    def _get_llm_response(self, input_text: str, prompt_type: PromptType) -> str:
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    def intent_manager(self) -> IntentManager | None:
        return self._intent_manager

    @intent_manager.setter
    def intent_manager(self, intent_manager: IntentManager) -> None:
        assert intent_manager.get_intent_length() > 1
        self._intent_manager = intent_manager
        self.__initialize_prompt_generator()

    def classify(
        self,
        input_text: str,
        prompt_type: PromptType | None = None,
    ) -> ClassifierResponse:
        if prompt_type is None:
            prompt_type = self._PROMPT_TYPE

        llm_output = self._get_llm_response(input_text, prompt_type)
        return ClassifierResponse(
            intent=self.intent_manager.get_closest_intent_simple(
                message=llm_output,
            ),
            llm_response=llm_output,
        )

    def __initialize_prompt_generator(self):
        if self._intent_manager is not None:
            self._prompt_generator = PromptGenerator(intent_manager=self._intent_manager)
