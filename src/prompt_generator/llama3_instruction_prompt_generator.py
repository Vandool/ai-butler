from __future__ import annotations

import datetime
import os
from abc import ABC, abstractmethod
from typing import ClassVar

import pytz
from dotenv import load_dotenv
from huggingface_hub import HfFolder
from transformers import AutoTokenizer

from src import utils
from src.prompt_generator.prompt_generator import PromptType
from src.web_handler.calendar_api import CalendarAPI
from src.web_handler.lecture_translator_api import LectureTranslatorApi

load_dotenv()
access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN", default="<TOKEN>")
chat_template_model = os.getenv("HUGGINGFACE_CHAT_TEMPLATE_MODEL", default="meta-llama/Meta-Llama-3-8B-Instruct")

# Save the token to the Hugging Face cache
HfFolder.save_token(access_token)


class ChatTemplateGenerator:
    def __init__(self, chat_template_model: str, access_token: str):
        self.tokenizer = AutoTokenizer.from_pretrained(
            chat_template_model,
            token=access_token,
        )

    def apply_chat_template(self, messages: list) -> str:
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


class PromptGeneratorLLama3Instruct(ABC):
    _SYS_PROMPT_FMT: ClassVar[str] = (
        "Below, you are presented with {n_candidates} candidate functions. Your task is to analyze a specific user input to "
        "determine which of these functions most appropriately addresses the query. Then, construct the correct function"
        " call with all necessary parameters, adhering to proper syntax. "
        "Format for function call: function_name(param1, param2, ...) "
        "Candidate Functions: \n"
        "{candidates}"
        "def irrelevant_function(): ”’If user query is not related to any of the predefined functions, this function will be called. Args: Returns: if the user asks a questiong about the history of the conversation, the question will be answered”’"
        "For time reference:"
        "Now: {now} which corresponds to {day_of_the_week}. "
        "You always reply with the following format:"
        '{{"text": "<your textual response>", "function_call": "<the function call>"}}'
        "You only reply with the above format and nothing else"
        "Your goal is to select the most suitable function out of the n_candidates candidates and generate an accurate function call that directly addresses the user's last input or the previous ones, if they are 100% related. Ensure the output is a syntactically valid function call. If the user asks a question about the history of your conversation, you can answer it based on the history.\n"
        "Here are some examples:\n"
        "{examples}\n"
    )

    def __init__(self, module: object | None = None):
        self.candidates = utils.get_candidates(module) if module else []
        self.chat_template_generator = ChatTemplateGenerator(
            chat_template_model=chat_template_model,
            access_token=access_token,
        )

    def generate_prompt(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT, history=None) -> str:
        """Generate a prompt based on the type specified."""
        return getattr(self, prompt_type.func_name)(input_text, history)

    def _generate_zero_shot_prompt(self, input_text: str, history) -> str:
        return self.chat_template_generator.apply_chat_template(
            messages=self.get_default_chat_messages(
                user_input=input_text,
                candidates=self.candidates,
                num_shots=0,
                extend_messages=history,
            ),
        )

    def _generate_zero_shot_detailed_prompt(self, input_text: str, history) -> str:
        """It's all detailed here"""
        return self._generate_zero_shot_prompt(input_text=input_text, history=history)

    def _generate_one_shot_per_class_detailed_prompt(self, input_text: str, history) -> str:
        return self.chat_template_generator.apply_chat_template(
            messages=self.get_default_chat_messages(
                user_input=input_text,
                candidates=self.candidates,
                num_shots=2 * 1,
                extend_messages=history,
            ),
        )

    def _generate_few_shot_per_class_detailed_prompt(self, input_text: str, history) -> str:
        return self.chat_template_generator.apply_chat_template(
            messages=self.get_default_chat_messages(
                user_input=input_text,
                candidates=self.candidates,
                num_shots=2 * 2,
                extend_messages=history,
            ),
        )

    @abstractmethod
    def get_default_chat_messages(
        self,
        user_input: str,
        candidates: list[str],
        extend_messages: list[dict] | None = None,
        num_shots: int = 0,
    ) -> list[dict]:
        pass


class CalendarAPIPromptGenerator(PromptGeneratorLLama3Instruct):
    def get_default_chat_messages(
        self,
        user_input: str,
        candidates: list[str],
        extend_messages: list[dict] | None = None,
        num_shots: int = 0,
    ) -> list[dict]:
        now_utc = datetime.datetime.now(datetime.UTC)
        berlin_tz = pytz.timezone("Europe/Berlin")
        now = now_utc.astimezone(berlin_tz)
        now = now.replace(minute=0, second=0, microsecond=0)
        twm = now + datetime.timedelta(days=1)
        tmw_14 = datetime.datetime(
            year=twm.year,
            month=twm.month,
            day=twm.day,
            hour=14,
            minute=0,
            second=0,
            tzinfo=berlin_tz,
        )
        next_week = now + datetime.timedelta(days=7)
        next_week_10 = datetime.datetime(
            year=next_week.year,
            month=next_week.month,
            day=next_week.day,
            hour=10,
            minute=0,
            second=0,
            tzinfo=berlin_tz,
        )

        shots = [
            {
                "role": "user",
                "content": "I want to create an appointment for tomorrow afternoon at 2 o'clock, it should take 2 hours of my time.",
            },
            {
                "role": "assistant",
                "content": f'{{"text": "Alright, I will create the appointment", "function_call": "create_new_appointment(\'Appointment\', \'{tmw_14.isoformat()!s}\', \'{(tmw_14 + datetime.timedelta(hours=2)).isoformat()!s}\')"}}',
            },
            {
                "role": "user",
                "content": "I want to create an appointment.",
            },
            {
                "role": "assistant",
                "content": '{"text": "Okey, can you tell me when should it start and end?", "function_call": "create_new_appointment(\'Appointment\', None, None)"}',
            },
            {
                "role": "user",
                "content": "I want to create an appointment for next week at at 10 o'clock.",
            },
            {
                "role": "assistant",
                "content": f'{{"text": "Okey, can you tell me when should it end?", "function_call": "create_new_appointment(\'Appointment\', \'{next_week_10.isoformat()!s}\', None)"}}',
            },
            {
                "role": "user",
                "content": "What is the timezone of my calendar?",
            },
            {
                "role": "assistant",
                "content": '{"text": "I assume the timezone should be by default your local timezone", "function_call": "irrelevant_function()"}',
            },
        ]

        messages = [
            {
                "role": "system",
                "content": self._SYS_PROMPT_FMT.format(
                    now=now.isoformat(),
                    day_of_the_week=now.strftime("%A"),
                    n_candidates=len(candidates) + 1,
                    candidates="\n".join(candidates),
                    examples="\n".join([f"{shot['role']}: {shot['content']}" for shot in shots[:num_shots]]),
                ),
            },
        ]

        if extend_messages:
            messages.extend(extend_messages)

        messages.append(
            {
                "role": "user",
                "content": f"{user_input}",
            },
        )
        return messages


class LectureAPIPromptGenerator(PromptGeneratorLLama3Instruct):
    def get_default_chat_messages(
        self,
        user_input: str,
        candidates: list[str],
        extend_messages: list[dict] | None = None,
        num_shots: int = 0,
    ) -> list[dict]:
        now_utc = datetime.datetime.now(datetime.UTC)
        now = now_utc.astimezone(pytz.timezone("Europe/Berlin"))
        now = now.replace(minute=0, second=0, microsecond=0)
        shots = [
            {
                "role": "user",
                "content": "user: What was the focus of the last lecture?",
            },
            {
                "role": "assistant",
                "content": '{"text": "Alright, I will retrieve the content of the last lecture for you.", "function_call": "get_lecture_content()"}',
            },
            {
                "role": "user",
                "content": "I need the lecture notes from the last session",
            },
            {
                "role": "assistant",
                "content": '{"text": "Sure, I will retrieve the transcript now.", "function_call": "get_lecture_content()"}',
            },
        ]

        messages = [
            {
                "role": "system",
                "content": self._SYS_PROMPT_FMT.format(
                    now=now.isoformat(),
                    day_of_the_week=now.strftime("%A"),
                    n_candidates=len(candidates) + 1,
                    candidates="\n".join(candidates),
                    examples="\n".join([f"{shot['role']}: {shot['content']}" for shot in shots[:num_shots]]),
                ),
            },
        ]

        if extend_messages:
            messages.extend(extend_messages)

        messages.append(
            {
                "role": "user",
                "content": f"{user_input}",
            },
        )
        return messages


class QAPromptGenerator(PromptGeneratorLLama3Instruct):
    _SYS_PROMPT_FMT: ClassVar[str] = (
        "Below, you are presented with {n_candidates} candidate functions. Your task is to analyze a specific user input to "
        "determine which of these functions most appropriately addresses the query. Then, construct the correct function"
        " call with all necessary parameters, adhering to proper syntax. "
        "Format for function call: function_name(param1, param2, ...) "
        "Candidate Functions: \n"
        "{candidates}"
        "def irrelevant_function(): ”’If user query is not related to any of the predefined functions, this function will be called. Args: Returns: if the user asks a questiong about the history of the conversation, the question will be answered”’"
        "For time reference:"
        "Now: {now} which corresponds to {day_of_the_week}"
        "You always reply with the following format:"
        '{{"text": "<your textual response>", "function_call": "<the function call>"}}'
        "You only reply with the above format and nothing else"
        "Ensure the output is a syntactically valid function call. If the user asks a question about the history of your conversation, you can answer it based on the history.\n"
        "Here are some examples:\n"
        "{examples}\n"
    )

    def get_default_chat_messages(
        self,
        user_input: str,
        candidates: list[str],
        extend_messages: list[dict] | None = None,
        num_shots: int = 0,
    ) -> list[dict]:
        now_utc = datetime.datetime.now(datetime.UTC)
        berlin_tz = pytz.timezone("Europe/Berlin")
        now = now_utc.astimezone(berlin_tz)
        now = now.replace(minute=0, second=0, microsecond=0)
        twm = now + datetime.timedelta(days=1)
        tmw_14 = datetime.datetime(
            year=twm.year,
            month=twm.month,
            day=twm.day,
            hour=14,
            minute=0,
            second=0,
            tzinfo=berlin_tz,
        )
        shots = [
            {
                "role": "user",
                "content": "I want to create an appointment for tomorrow afternoon at 2 o'clock, it should take 2 hours of my time.",
            },
            {
                "role": "assistant",
                "content": f'{{"text": "Alright, I will create the appointment", "function_call": "create_new_appointment(\'Appointment\', \'{tmw_14.isoformat()!s}\', \'{(tmw_14 + datetime.timedelta(hours=2)).isoformat()!s}\')"}}',
            },
            {
                "role": "user",
                "content": "What's on my schedule for today?",
            },
            {
                "role": "assistant",
                "content": '{"text": "Today you have no scheduled appointments. Enjoy your free time!", "function_call": "get_next_appointment()"}',
            },
            {
                "role": "user",
                "content": "At what time the last appointment we've created start again?",
            },
            {
                "role": "assistant",
                "content": "The last appointment you have create will start tomorrow at two o'clock and it would last about two hours.",
            },
        ]
        messages = [
            {
                "role": "system",
                "content": self._SYS_PROMPT_FMT.format(
                    now=now.isoformat(),
                    day_of_the_week=now.strftime("%A"),
                    n_candidates=len(candidates) + 1,
                    candidates="\n".join(candidates) if candidates else "",
                    examples="\n".join([f"{shot['role']}: {shot['content']}" for shot in shots]),
                ),
            },
        ]
        if extend_messages:
            messages.extend(extend_messages)

        messages.append(
            {
                "role": "user",
                "content": f"{user_input}",
            },
        )
        return messages


def get_prompt_generator(api: CalendarAPI | LectureTranslatorApi | None) -> PromptGeneratorLLama3Instruct:
    if isinstance(api, CalendarAPI):
        return CalendarAPIPromptGenerator(module=api)
    if isinstance(api, LectureTranslatorApi):
        return LectureAPIPromptGenerator(module=api)
    return QAPromptGenerator()
