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
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManagerFactory
from src.intent.slot_filler import SlotFillerSimple
from src.llm_client.llm_client import LLMClient
from src.prompt_generator import respond_prompts
from src.prompt_generator.prompt_generator import PromptType
from src.text2speech.microsoft_speecht5_tts import TextToSpeech
from src.utils import FunctionInfo
from src.web_handler.calendar_api import CalendarAPI

FunctionName: TypeAlias = str


def _add_time_now_to(fn_response):
    fn_response.update({"now": datetime.datetime.now(datetime.UTC)})
    return fn_response


class State(abc.ABC):
    def __init__(self, llm_client: LLMClient, classifier: BaseClassifier, tts_client: TextToSpeech | None = None):
        super().__init__()
        self.llm_client = llm_client
        self.logger = utils.get_logger(self.__class__.__name__)
        self.classifier = classifier
        self.tts_client = tts_client

    @abc.abstractmethod
    def process(self, user_input: str) -> State:
        pass

    @abc.abstractmethod
    def get_clarify_prompt(self, last_input: str) -> str:
        pass

    def clarify(self, last_input: str):
        llm_response = self.llm_client.get_response(
            prompt=self.get_clarify_prompt(last_input=last_input),
        )
        self.logger.info(llm_response)
        self.text_to_speech(llm_response)

    def text_to_speech(self, text: str) -> None:
        if self.tts_client:
            self.tts_client.text_to_speech(text)

    @staticmethod
    def found_no_intent(current_intent: Intent) -> bool:
        return current_intent in (None, intent.UNKNOWN)

    def output(self, response: str) -> None:
        self.logger.info(response)
        self.text_to_speech(response)


class InitialState(State):
    KEYWORDS: ClassVar[list[str]] = ["ok butler", "okay butler", "hey butler", "butler", "bottler"]

    def __init__(self, llm_client: LLMClient, tts_client: TextToSpeech | None = None):
        super().__init__(
            llm_client=llm_client,
            classifier=FewShotTextGenerationClassifier(
                llm_client=llm_client,
                intent_manager=IntentManagerFactory.get_intent_manager_with_unknown_intent(),
            ),
            tts_client=tts_client,
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
        self.logger.info(f"\tLLM Output: {classifier_response.llm_response}")
        self.logger.info(f"\tIntention Class: {classifier_response.intent.name}")

        if classifier_response.intent == intent.CALENDAR:
            return CalendarState(llm_client=self.llm_client, tts_client=self.tts_client).process(user_input)
        if classifier_response.intent == intent.LECTURE:
            return LectureState(llm_client=self.llm_client, tts_client=self.tts_client).process(user_input)

        self.clarify(last_input=user_input)
        return self

    def get_clarify_prompt(self, last_input: str) -> None:
        return respond_prompts.INIT_STATE_REPEAT_FMT.format(
            last_utterance=last_input,
        )


class CalendarState(State):
    def __init__(self, llm_client: LLMClient, tts_client: TextToSpeech | None = None):
        self.api = CalendarAPI()
        super().__init__(
            llm_client=llm_client,
            classifier=generate_classifier(module=self.api, llm_client=llm_client),
            tts_client=tts_client,
        )
        self.slot_filler: SlotFillerSimple | None = None
        self.function_info: dict[FunctionName, FunctionInfo] | None = utils.get_marked_functions_and_docstrings(
            module=self.api,
        )
        self._current_intent: Intent | None = None

    @property
    def current_intent(self) -> Intent:
        return self._current_intent

    @current_intent.setter
    def current_intent(self, user_intent: Intent):
        self._current_intent = user_intent

    def process(self, user_input: str) -> State:
        if self._in_slot_filling_process():
            return self._process_slot_filling(user_input)

        return self._process_intent_classification(user_input)

    def _process_slot_filling(self, user_input: str) -> State:
        self.slot_filler.process(user_input)
        if not self.slot_filler.is_done:
            return self

        self._call_intended_function(user_input, **self.slot_filler.get_kwargs())
        return InitialState(llm_client=self.llm_client, tts_client=self.tts_client)

    def _process_intent_classification(self, user_input: str) -> State:
        classifier_response = self.classifier.classify(
            input_text=user_input,
            prompt_type=PromptType.FEW_SHOT_DETAILED,
        )
        self.logger.info(f"\tLLM Output: {classifier_response.llm_response}")
        self.logger.info(f"\tIntention Class: {classifier_response.intent.name}")

        if self.found_no_intent(current_intent=classifier_response.intent):
            self.clarify(last_input=user_input)
            return self

        self.current_intent = classifier_response.intent

        if self._slot_filling_required(fn_name=self.current_intent.name):
            self._start_slot_filling(user_input)
            return self

        self._call_intended_function(user_input)
        return InitialState(llm_client=self.llm_client, tts_client=self.tts_client)

    def _start_slot_filling(self, user_input: str) -> None:
        self.slot_filler = SlotFillerSimple(
            func=self.get_intended_function(),
            llm_client=self.llm_client,
            text_to_speech=self.tts_client,
        )
        self.slot_filler.process(user_input)

    def get_intended_function(self):
        if self.current_intent is None:
            msg = "No current intent set."
            raise ValueError(msg)
        return getattr(self.api, self.current_intent.name)

    def _in_slot_filling_process(self):
        return self.slot_filler is not None

    def _call_intended_function(self, user_input: str, **kwargs) -> None:
        intended_fn = self.get_intended_function()

        self.logger.info(f"Calling `{intended_fn.__name__}` ...")
        fn_response = intended_fn(**kwargs)

        if isinstance(fn_response, dict):
            fn_response = _add_time_now_to(fn_response)

        llm_prompt = respond_prompts.get_calendar_api_respond_prompts(self.current_intent.name).format(
            last_utterance=user_input,
            function_response=fn_response,
        )
        self.logger.debug(llm_prompt)

        self.output(response=(self.llm_client.get_response(prompt=llm_prompt)))

    def get_clarify_prompt(self, last_input: str) -> None:
        return respond_prompts.INIT_STATE_REPEAT_FMT.format(
            last_utterance=last_input,
        )

    def _slot_filling_required(self, fn_name: str) -> bool:
        if fn_name in self.function_info:
            return self.function_info[fn_name].has_slots
        return False


class LectureState(State):
    def __init__(self, llm_client: LLMClient, tts_client: TextToSpeech | None = None):
        self.api = CalendarAPI()
        super().__init__(
            llm_client=llm_client,
            classifier=generate_classifier(module=self.api, llm_client=llm_client),
            tts_client=tts_client,
        )

    def get_clarify_prompt(self, last_input: str) -> str:
        pass

    def process(self, user_input: str) -> State:
        pass


if __name__ == "__main__":
    state = InitialState(llm_client=LLMClient(client=AsrLlmConfig.llm_url))
    print(state._trim_transcript("Hey Butler, what are we doing next?"))
