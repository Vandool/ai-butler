from __future__ import annotations

import abc

from src import utils
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptGenerator, PromptType


class BaseClassifier(abc.ABC):
    def __init__(self):
        self.logger = utils.get_logger(self.__class__.__name__)
        self._intent_manager: IntentManager | None = None
        self._prompt_generator: PromptGenerator | None = None

    @abc.abstractmethod
    def classify(self, input_text: str, prompt_type: str = "simple") -> str:
        pass

    @abc.abstractmethod
    def classify_with_details(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
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

    def get_closest_intent_using_similarity(
        self,
        input_text: str,
        prompt_type: PromptType = PromptType.ZERO_SHOT,
    ) -> Intent:
        # TODO(Arvand): the one shot classifier doesn't need this. depending on what we choose in the end we can
        # delete this
        return self.intent_manager.get_closest_intent_similarity(
            message=self.classify(input_text, prompt_type),
        )

    def get_closest_intent_simple(
        self,
        input_text: str,
        prompt_type: PromptType = PromptType.ZERO_SHOT,
    ) -> (Intent, str):
        # TODO(Arvand): the one shot classifier doesn't need this. depending on what we choose in the end we can delete
        llm_output = self.classify(input_text, prompt_type)
        return self.intent_manager.get_closest_intent_simple(
            message=llm_output,
        ), llm_output

    def __initialize_prompt_generator(self):
        if self._intent_manager is not None:
            self._prompt_generator = PromptGenerator(intent_manager=self._intent_manager)
            # self._prompt_generator = Llama2PromptGenerator(intent_manager=self._intent_manager)
