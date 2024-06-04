from __future__ import annotations

import abc
import datetime
from typing import ClassVar, TypeAlias

from fuzzywuzzy import fuzz

from src import utils
from src.classifier.base_classifier import BaseClassifier
from src.classifier.classifier_generator import generate_classifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.config.asr_llm_config import AsrLlmConfig
from src.intent import intent
from src.intent.intent_manager import IntentManagerFactory
from src.intent.slot_filler import SlotFillerSimple
from src.llm_client.llm_client import LLMClient
from src.prompt_generator import respond_prompts
from src.prompt_generator.prompt_generator import PromptType
from src.utils import FunctionInfo
from src.web_handler.calendar_api import CalendarAPI

FunctionName: TypeAlias = str


def _add_time_now_to(fn_response):
    fn_response.update({"now": datetime.datetime.now(datetime.UTC)})
    return fn_response


class State(abc.ABC):
    def __init__(self, llm_client: LLMClient, classifier: BaseClassifier):
        super().__init__()
        self.llm_client = llm_client
        self.logger = utils.get_logger(self.__class__.__name__)
        self.classifier = classifier

    @abc.abstractmethod
    def process(self, user_input: str) -> State:
        pass

    @abc.abstractmethod
    def clarify(self):
        pass


class InitialState(State):
    KEYWORDS: ClassVar[list[str]] = ["ok butler", "okay butler", "hey butler", "butler", "bottler"]

    def __init__(self, llm_client: LLMClient):
        super().__init__(
            llm_client=llm_client,
            classifier=FewShotTextGenerationClassifier(
                llm_client=llm_client,
                intent_manager=IntentManagerFactory.get_intent_manager_with_unknown_intent(),
            ),
        )

    def process(self, user_input: str) -> State:
        next_state = self
        if self._keyword_spotting(user_input):
            self.logger.info("Keyword spotted, sending to classifier.")
            trimmed_transcript = self._trim_transcript(user_input)
            self.logger.info(f"Trimmed sequence: {trimmed_transcript}")
            next_state = self._check_and_send_to_classifier(trimmed_transcript)
        else:
            self.logger.info("No keyword detected.")
        return next_state

    @staticmethod
    def _keyword_spotting(transcript: str) -> bool:
        # TODO: maybe we can use a classifier here? as improvement?
        transcript = transcript.lower()
        return any(fuzz.partial_ratio(transcript, keyword) > 80 for keyword in InitialState.KEYWORDS)

    @staticmethod
    def _trim_transcript(transcript: str) -> str:
        lower_transcript = transcript.lower()
        for keyword in InitialState.KEYWORDS:
            if keyword in lower_transcript:
                return transcript[lower_transcript.find(keyword) + len(keyword) :].lstrip(" ,;:")
        return transcript.strip()

    def _check_and_send_to_classifier(self, user_input: str) -> State:
        classifier_response = self.classifier.classify(
            input_text=user_input,
            prompt_type=PromptType.FEW_SHOT_DETAILED,
        )
        if classifier_response.intent == intent.CALENDAR:
            return CalendarState(llm_client=self.llm_client).process(user_input)
        if classifier_response.intent == intent.LECTURE:
            return LectureState(llm_client=self.llm_client).process(user_input)
        self.clarify()
        return self

    def clarify(self):
        # TODO: This part can be generated using the llm
        self.logger.info("Sorry, I didnt' quite catch what you said, could please repeat that?")


class CalendarState(State):
    def __init__(self, llm_client: LLMClient):
        self.api = CalendarAPI()
        super().__init__(llm_client=llm_client, classifier=generate_classifier(module=self.api, llm_client=llm_client))
        self.slot_filler: SlotFillerSimple | None = None
        self.function_info: dict[FunctionName, FunctionInfo] | None = utils.get_marked_functions_and_docstrings(
            module=self.api,
        )

    def process(self, user_input: str) -> State:
        if self.slot_filler is None:
            classifier_response = self.classifier.classify(
                input_text=user_input,
                prompt_type=PromptType.FEW_SHOT_DETAILED,
            )
            if classifier_response.intent in (None, intent.UNKNOWN):
                self.clarify()
                return self

            fn_name = classifier_response.intent.name
            intended_fn = getattr(self.api, fn_name)
            if self._slot_filling_required(fn_name=fn_name):
                # Otherwise start the slot filling process
                self.slot_filler = SlotFillerSimple(
                    func=intended_fn,
                    llm_client=self.llm_client,
                )
            else:
                self.logger.info(f"Calling '{intended_fn.__name__}' function:")
                fn_response = intended_fn()
                self.logger.info(fn_response)
                if fn_response:
                    fn_response = _add_time_now_to(fn_response)
                llm_prompt = respond_prompts.get_calendar_api_respond_prompts(fn_name).format(
                    last_utterance=user_input,
                    function_response=fn_response,
                )
                self.logger.info(llm_prompt)
                llm_respond = self.llm_client.get_response(prompt=llm_prompt)
                self.logger.info(
                    llm_respond,
                )
        # TODO: "Need to implement the rest, taking care of slot filling"
        return InitialState(llm_client=self.llm_client)

    def clarify(self):
        # TODO: This part can be generated using the llm
        self.logger.info("Sorry, I didnt' quite catch what you said, could please repeat that?")

    def _slot_filling_required(self, fn_name: str) -> bool:
        if fn_name in self.function_info:
            return self.function_info[fn_name].has_slots
        return False


class LectureState(State):
    def __init__(self, llm_client: LLMClient):
        self.api = CalendarAPI()
        super().__init__(llm_client=llm_client, classifier=generate_classifier(module=self.api, llm_client=llm_client))

    def clarify(self):
        pass

    def process(self, user_input: str) -> State:
        pass


if __name__ == "__main__":
    state = InitialState(llm_client=LLMClient(client=AsrLlmConfig.llm_url))
    print(state._trim_transcript("Hey Butler, what are we doing next?"))
