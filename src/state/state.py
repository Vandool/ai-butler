from __future__ import annotations

import abc
import datetime
import json
from typing import ClassVar, TypeAlias

import pytz
from fuzzywuzzy import fuzz
from huggingface_hub import InferenceClient

from src import utils
from src.classifier.base_classifier import BaseClassifier
from src.classifier.classifier_generator import generate_classifier, generate_function_caller_classifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.config.asr_llm_config import AsrLlmConfig
from src.history.chathistory import ChatHistory, Message, Role
from src.intent import intent
from src.intent.intent import UNKNOWN, Intent
from src.intent.intent_manager import IntentManagerFactory
from src.intent.slot_filler import SlotFillerAdvanced, SlotFillerSimple
from src.llm_client.llm_client import LLMClient
from src.prompt_generator import respond_prompts
from src.prompt_generator.prompt_generator import PromptType
from src.text2speech.microsoft_speecht5_tts import TextToSpeech
from src.utils import FunctionInfo
from src.web_handler.calendar_api import CalendarAPI
from src.web_handler.lecture_translator_api import LectureTranslatorAPI

FunctionName: TypeAlias = str


def add_time_now_to(fn_response):
    now_utc = datetime.datetime.now(datetime.UTC)
    now = now_utc.astimezone(pytz.timezone("Europe/Berlin"))
    fn_response.update({"now": now.replace(minute=0, second=0, microsecond=0)})
    return fn_response


class State(abc.ABC):
    def __init__(
        self,
        llm_client: LLMClient,
        classifier: BaseClassifier,
        tts_client: TextToSpeech | None = None,
        history: ChatHistory | None = None,
    ):
        super().__init__()
        self.llm_client = llm_client
        self.logger = utils.get_logger(self.__class__.__name__)
        self.classifier = classifier
        self.tts_client = tts_client
        self._history = history

    @property
    def history(self) -> ChatHistory:
        return self._history

    @history.setter
    def history(self, history: ChatHistory):
        self._history = history

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

        if self.history:
            self.history.add_message(
                Message(text=llm_response, role=Role.ASSISTANT),
            )

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

    def __init__(
        self,
        llm_client: LLMClient,
        tts_client: TextToSpeech | None = None,
        history: ChatHistory | None = None,
        *,
        use_function_caller: bool = False,
    ):
        super().__init__(
            llm_client=llm_client,
            classifier=FewShotTextGenerationClassifier(
                llm_client=llm_client,
                intent_manager=IntentManagerFactory.get_intent_manager_with_unknown_intent(),
            ),
            tts_client=tts_client,
            history=history,
        )
        self.message = Message()
        self.use_function_caller = use_function_caller

    def process(self, user_input: str) -> State:
        next_state = self
        if self._keyword_spotting(user_input):
            if self.history:
                self.message = self.message.set_text(user_input).set_role(Role.USER)

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

        if self.history:
            self.message = self.message.set_classifier_response_level_0(classifier_response)
            self.history.add_message(self.message)
        if not self.use_function_caller:
            if classifier_response.intent == intent.CALENDAR:
                return CalendarState(
                    llm_client=self.llm_client,
                    tts_client=self.tts_client,
                    history=self.history,
                ).process(
                    user_input,
                )
            if classifier_response.intent == intent.LECTURE:
                return LectureState(
                    llm_client=self.llm_client,
                    tts_client=self.tts_client,
                    history=self.history,
                ).process(
                    user_input,
                )
        else:
            if classifier_response.intent == intent.CALENDAR:
                return FunctionCallerState(
                    llm_client=self.llm_client,
                    tts_client=self.tts_client,
                    history=self.history,
                    api=CalendarAPI(),
                ).process(
                    user_input,
                )
            if classifier_response.intent == intent.LECTURE:
                return FunctionCallerState(
                    llm_client=self.llm_client,
                    tts_client=self.tts_client,
                    history=self.history,
                    api=LectureTranslatorAPI(),
                ).process(
                    user_input,
                )
            if classifier_response.intent == intent.CHAT_HISTORY:
                return FunctionCallerState(
                    llm_client=self.llm_client,
                    tts_client=self.tts_client,
                    history=self.history,
                ).process(
                    user_input,
                )

        self.clarify(last_input=user_input)
        return self

    def get_clarify_prompt(self, last_input: str) -> None:
        return respond_prompts.INIT_STATE_REPEAT_FMT.format(
            last_utterance=last_input,
        )


class CalendarState(State):
    def __init__(
        self,
        llm_client: LLMClient,
        tts_client: TextToSpeech | None = None,
        history: ChatHistory | None = None,
    ):
        self.api = CalendarAPI()
        super().__init__(
            llm_client=llm_client,
            classifier=generate_classifier(module=self.api, llm_client=llm_client),
            tts_client=tts_client,
            history=history,
        )
        self.slot_filler: SlotFillerSimple | None = None
        self.function_info: dict[FunctionName, FunctionInfo] | None = utils.get_marked_functions_and_docstrings(
            module=self.api,
        )
        self._current_intent: Intent | None = None
        if self.history:
            self.message = Message()

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

        # Extend history wish slot filler's history
        if self.history:
            self.history.add_history(self.slot_filler.history)

        self._call_intended_function(user_input, **self.slot_filler.get_kwargs())
        return InitialState(llm_client=self.llm_client, tts_client=self.tts_client, history=self.history)

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
        if self.history:
            self.message = Message()

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

    def _function_name_helper(self, fn_name):
        pass

    def _call_intended_function(self, user_input: str, **kwargs) -> None:
        intended_fn = self.get_intended_function()
        self._function_name_helper(intended_fn.__name__)

        self.logger.info(f"Calling `{intended_fn.__name__}` ...")
        fn_response = intended_fn(**kwargs)

        if isinstance(fn_response, dict):
            fn_response = add_time_now_to(fn_response)
        elif isinstance(fn_response, list):
            fn_response = [add_time_now_to(res) for res in fn_response]

        llm_prompt = respond_prompts.get_api_respond_prompts(self.current_intent.name).format(
            last_utterance=user_input,
            function_response=fn_response,
        )
        self.logger.debug(llm_prompt)

        # Open the html link
        # self.api.open_html_link(response=fn_response)

        response = self.llm_client.get_response(prompt=llm_prompt)
        if self.history:
            self.history.add_message(
                self.message.set_text(text=response)
                .set_role(Role.ASSISTANT)
                .set_function_call(function_call=self.current_intent.name)
                .set_function_args(kwargs.items())
                .set_function_response(fn_response),
            )

        self.output(response=response)

    def get_clarify_prompt(self, last_input: str) -> None:
        return respond_prompts.INIT_STATE_REPEAT_FMT.format(
            last_utterance=last_input,
        )

    def _slot_filling_required(self, fn_name: str) -> bool:
        if fn_name in self.function_info:
            return self.function_info[fn_name].has_slots
        return False


class LectureState(State):
    def __init__(
        self,
        llm_client: LLMClient,
        tts_client: TextToSpeech | None = None,
        history: ChatHistory | None = None,
    ):
        self.api = LectureTranslatorAPI()
        super().__init__(
            llm_client=llm_client,
            classifier=generate_classifier(module=self.api, llm_client=llm_client),
            tts_client=tts_client,
            history=history,
        )

    def get_clarify_prompt(self, last_input: str) -> str:
        pass

    @property
    def current_intent(self) -> Intent:
        return self._current_intent

    @current_intent.setter
    def current_intent(self, user_intent: Intent):
        self._current_intent = user_intent

    def process(self, user_input: str) -> State:
        return self._process_intent_classification(user_input)

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
        if self.history:
            self.message = Message()

        self._call_intended_function(user_input)
        return InitialState(llm_client=self.llm_client, tts_client=self.tts_client)

    def get_intended_function(self):
        if self.current_intent is None:
            msg = "No current intent set."
            raise ValueError(msg)
        return getattr(self.api, self.current_intent.name)

    def _function_name_helper(self, fn_name):
        pass

    def _call_intended_function(self, user_input: str, **kwargs) -> None:
        intended_fn = self.get_intended_function()
        self._function_name_helper(intended_fn.__name__)

        self.logger.info(f"Calling `{intended_fn.__name__}` ...")
        fn_response = intended_fn(**kwargs)

        if isinstance(fn_response, dict):
            fn_response = add_time_now_to(fn_response)
        elif isinstance(fn_response, list):
            fn_response = [add_time_now_to(res) for res in fn_response]

        llm_prompt = respond_prompts.get_lecture_api_respond_prompts(self.current_intent.name).format(
            last_utterance=user_input,
            function_response=fn_response,
        )
        self.logger.debug(llm_prompt)

        # Open the html link
        # self.api.open_html_link(response=fn_response)

        response = self.llm_client.get_response(prompt=llm_prompt)
        if self.history:
            self.history.add_message(
                self.message.set_text(text=response)
                .set_role(Role.ASSISTANT)
                .set_function_call(function_call=self.current_intent.name)
                .set_function_args(kwargs.items())
                .set_function_response(fn_response),
            )

        self.output(response=response)


class FunctionCallerState(State):
    def __init__(
        self,
        llm_client: LLMClient,
        tts_client: TextToSpeech | None = None,
        history: ChatHistory | None = None,
        api: CalendarAPI | LectureTranslatorAPI | None = None,
    ):
        self.api = api
        super().__init__(
            llm_client=llm_client,
            classifier=generate_function_caller_classifier(api=self.api, llm_client=llm_client),
            tts_client=tts_client,
            history=history,
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
        if self.slot_filler is not None and self.history is not None:
            self.history.add_message(Message().set_text(user_input).set_role(Role.USER))

        classifier_response = self.classifier.classify(
            input_text=user_input,
            prompt_type=PromptType.FEW_SHOT_DETAILED,
            history=self.history.get_level_1_history(),
        )
        self.logger.info("------------LLM Response--------------------")
        self.logger.info(classifier_response.llm_response)
        self.logger.info("------------Intent Class--------------------")
        self.logger.info(classifier_response.intent.name)
        self.logger.info("--------------------------------------------")

        try:
            llm_json = utils.extract_json(classifier_response.llm_response)
        except (json.decoder.JSONDecodeError, TypeError, ValueError):
            # if self.found_no_intent(current_intent=classifier_response.intent):
            self.clarify(last_input=user_input)
            return self

        # Remove assert later
        self.current_intent = classifier_response.intent
        function_call_info = utils.parse_function_call(llm_json["function_call"])

        if self.history:
            self.history.set_classifier_response_level_1(classifier_response=classifier_response)

        # Handle Unknown case
        if classifier_response.intent == UNKNOWN:
            output = llm_json["text"]
            if self.history:
                self.history.add_message(Message().set_text(output).set_role(Role.ASSISTANT))
            self.output(response=output)
            return InitialState(llm_client=self.llm_client, tts_client=self.tts_client, use_function_caller=True)

        if self.slot_filler is not None or self._slot_filling_required(
            fn_name=self.current_intent.name,
        ):
            self.slot_filler = SlotFillerAdvanced(
                func=self.get_intended_function(),
                function_params=function_call_info.parameters,
            )
            if self.slot_filler.is_done:
                self._call_intended_function(user_input, **self.slot_filler.get_kwargs())
                return InitialState(llm_client=self.llm_client, tts_client=self.tts_client, use_function_caller=True)

            output = llm_json["text"]
            if self.history:
                self.history.add_message(Message().set_text(output).set_role(Role.ASSISTANT))
            self.output(response=output)
            return self

        self._call_intended_function(user_input)
        return InitialState(llm_client=self.llm_client, tts_client=self.tts_client, use_function_caller=True)

    def get_intended_function(self):
        if self.current_intent is None:
            msg = "No current intent set."
            raise ValueError(msg)
        return getattr(self.api, self.current_intent.name)

    def _in_slot_filling_process(self):
        return self.slot_filler is not None

    def _function_name_helper(self, fn_name):
        pass

    def _call_intended_function(self, user_input: str, **kwargs) -> None:
        intended_fn = self.get_intended_function()
        self._function_name_helper(intended_fn.__name__)

        self.logger.info(f"Calling `{intended_fn.__name__}` ...")
        fn_response = intended_fn(**kwargs)

        if isinstance(fn_response, dict):
            fn_response = add_time_now_to(fn_response)
        elif isinstance(fn_response, list):
            fn_response = [add_time_now_to(res) for res in fn_response]

        llm_prompt = respond_prompts.get_api_respond_prompts(self.current_intent.name).format(
            last_utterance=user_input,
            function_response=fn_response,
        )
        self.logger.debug(llm_prompt)

        # Open the html link
        # self.api.open_html_link(response=fn_response)

        response = self.llm_client.get_response(prompt=llm_prompt)
        if self.history:
            self.history.add_message(
                Message()
                .set_text(text=response)
                .set_role(Role.ASSISTANT)
                .set_function_call(function_call=self.current_intent.name)
                .set_function_args(kwargs.items())
                .set_function_response(fn_response),
            )

        self.output(response=response)

    def get_clarify_prompt(self, last_input: str) -> None:
        return respond_prompts.INIT_STATE_REPEAT_FMT.format(
            last_utterance=last_input,
        )

    def _slot_filling_required(self, fn_name: str) -> bool:
        if fn_name in self.function_info:
            return self.function_info[fn_name].has_slots
        return False


if __name__ == "__main__":
    # inference_client = InferenceClient(model="maywell/Llama-3-Ko-8B-Instruct", token=os.environ["HF_TOKEN"])
    inference_client = LLMClient(client=InferenceClient(AsrLlmConfig.llm_url))
    state = InitialState(llm_client=inference_client)
    print(state.process("Hey Butler, please summarize the last lecture."))
