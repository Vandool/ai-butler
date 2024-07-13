from __future__ import annotations

import abc
from dataclasses import dataclass

from src import utils
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient
from src.prompt_generator.llama3_instruction_prompt_generator import (
    CalendarAPIPromptGenerator,
    PromptGeneratorLLama3Instruct,
)
from src.prompt_generator.llama3_prompt_generator import Llama3PromptGenerator
from src.prompt_generator.prompt_generator import PromptGeneratorLlama2, PromptType


@dataclass
class ClassifierResponse:
    intent: Intent | None = None
    llm_response: str | None = None


class BaseClassifier(abc.ABC):
    _PROMPT_TYPE: PromptType = PromptType.FEW_SHOT_DETAILED

    def __init__(self):
        self.logger = utils.get_logger(self.__class__.__name__)
        self._intent_manager: IntentManager | None = None
        self._prompt_generator: PromptGeneratorLlama2 | CalendarAPIPromptGenerator | None = None

    @property
    def prompt_generator(self) -> PromptGeneratorLlama2 | CalendarAPIPromptGenerator | None:
        return self._prompt_generator

    @prompt_generator.setter
    def prompt_generator(self, prompt_generator: PromptGeneratorLlama2 | CalendarAPIPromptGenerator):
        self._prompt_generator = prompt_generator

    @classmethod
    def set_prompt_type(cls, prompt_type: PromptType) -> None:
        cls._PROMPT_TYPE = prompt_type

    @abc.abstractmethod
    def _get_llm_response(self, input_text: str, prompt_type: PromptType, history: list[dict] | None = None) -> str:
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
        # assert intent_manager.get_intent_length() > 1
        self._intent_manager = intent_manager
        self.__initialize_prompt_generator()

    def classify(
        self,
        input_text: str,
        prompt_type: PromptType | None = None,
        history: list[dict] | None = None,
    ) -> ClassifierResponse:
        if prompt_type is None:
            prompt_type = self._PROMPT_TYPE

        llm_output = self._get_llm_response(input_text, prompt_type, history)

        # Special case handling
        if isinstance(self, FunctionCallClassifier):
            function_name = utils.parse_function_call(text=llm_output).function_name
        else:
            function_name = llm_output

        return ClassifierResponse(
            intent=self.intent_manager.get_closest_intent_simple(
                message=function_name,
            ),
            llm_response=llm_output,
        )

    def __initialize_prompt_generator(self):
        if self._intent_manager is not None:
            self.prompt_generator = Llama3PromptGenerator(intent_manager=self._intent_manager)


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
            max_new_tokens=128,
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text


class FunctionCallClassifier(BaseClassifier):
    def __init__(
        self,
        prompt_generator: PromptGeneratorLLama3Instruct,
        llm_client: LLMClient,
        intent_manager: IntentManager | None = None,
    ):
        super().__init__()
        self.llm_client = llm_client
        self.intent_manager = intent_manager
        self.prompt_generator = prompt_generator

    @property
    def name(self) -> str:
        return "function_call_classifier"

    def _get_llm_response(self, input_text: str, prompt_type: PromptType, history: list[dict] | None = None) -> str:
        prompt = self.prompt_generator.generate_prompt(input_text, prompt_type=prompt_type, history=history)
        self.logger.info("------------Prompt--------------------")
        self.logger.info(prompt)
        generated_text = self.llm_client.get_response(
            prompt=prompt,
            max_new_tokens=128,
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text
