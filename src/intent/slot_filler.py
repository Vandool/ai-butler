from __future__ import annotations

import datetime
import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from huggingface_hub import InferenceClient

from src import utils
from src.config.asr_llm_config import get_asr_llm_config
from src.history.history import History
from src.llm_client.llm_client import LLMClient
from src.text2speech.microsoft_speecht5_tts import TextToSpeech
from src.web_handler.calendar_api import CalendarAPI


@dataclass
class Slot:
    name: str
    param_type: type
    is_required: bool
    # Idea: based on the attempts made we can modify the prompt to ask more specific question
    attempts: int = 0
    value: Any = None
    is_set: bool = field(default=False, init=False)

    def set_value(self, value: Any):
        # TODO(Arvand): Here we neeed type checking, we need a proper setter, maybe using llm
        self.value = value
        self.is_set = True
        self.attempts += 1

    def get_name_value(self):
        return {"name": self.name, "value": self.value}

    def get_kwarg(self) -> dict:
        return {self.name: self.value}

    def __str__(self):
        return str(json.dumps(self.__dict__, indent=2))


def extract_slots_from_function(func) -> list[Slot]:
    sig = inspect.signature(func)
    slots = []
    for param in sig.parameters.values():
        required = param.default is param.empty
        slots.append(Slot(param.name, param.annotation, required))
    return slots


_GREETING_PROMPT_FMT = """
<s>[INST] <<SYS>>
You are a professional python developer specialised in the package datetime.
You can convert natural language dates into datetime functions

Example:
text: today at 9 o'clock
answer: Alright, let's create an appointment.

Greet them with one very short sentence.
Do not ask user any question! I repeat, do not ask any questions.

Text: {purpose}
<</SYS>> [/INST]
AI:
"""


class SlotFillerSimple:
    _DEFAULT_TEMPLATE_FMT = """
<s>[INST] <<SYS>>
You are an AI assistant helping a human to {purpose}.

The following is a friendly conversation between a human and an AI.
You are very precise and response very briefly.
If the AI does not know the answer to a question, it truthfully says it does not know.

The Current Slots show all the information you need to {purpose}.
{slot_instructions}

If the Information check is True, it means that all the information required for {purpose} has been collected, the AI should output "Alright, now we can {purpose}".

Do not repeat the human's response!
Do not output the Current Slots!
Do not tell the user why you are asking a question about the appointment.
Do not suggest the user how they should reply.

Current conversation:
{history}
Current Slots:
{slots}
Human: {input}
<</SYS>> [/INST]
AI:
"""
    _GREETING_PROMPT_FMT = """
<s>[INST] <<SYS>>
You are an AI assistant and welcome the human to the conversation and greet them very briefly.

Example:
text: create_an_appointment
AI: Alright, let's create an appointment.

Greet them with one very short sentence.
Do not ask user any question! I repeat, do not ask any questions.

Text: {purpose}
<</SYS>> [/INST]
AI:
"""
    _SLOT_INSTRUCTION_FMT = "If {name} is None with respect to the Current Slots 'value', ask a question about the {name} of the appointment."

    def __init__(self, func: Callable, llm_client: LLMClient, text_to_speech: TextToSpeech | None = None):
        self.purpose: str = func.__name__
        self.slots: list[Slot] = extract_slots_from_function(func)
        self.history: History = History()
        self.logger = utils.get_logger("SlotFiller")
        self.is_greeting: bool = True
        self.llm_client = llm_client
        self.tts = text_to_speech
        self.is_just_started = True

    @property
    def is_done(self) -> bool:
        return all(slot.is_set for slot in self.slots)

    @property
    def _next_slot(self) -> Slot | None:
        for slot in self.slots:
            if not slot.is_set:
                return slot
        return None

    def _generate_prompt(self, user_input: str) -> str:
        slot_instructions = self._SLOT_INSTRUCTION_FMT.format(name=self._next_slot.name)
        current_slots_str = self._next_slot.get_name_value()
        history_str = self.history.get_history()

        return self._DEFAULT_TEMPLATE_FMT.format(
            purpose=self.purpose,
            slot_instructions=slot_instructions,
            history=history_str,
            slots=current_slots_str,
            input=user_input,
        )

    def process(self, user_input: str) -> str:
        if not self.is_just_started:
            self.fill_slot(user_input=user_input)
        else:
            self.is_just_started = True

        self.history.add_human_message(user_input)
        self.logger.info(f"Handling user input '{user_input}' ...")
        llm_response = self.llm_client.get_response(prompt=self._generate_prompt(user_input))
        self.history.add_ai_message(llm_response)
        self.logger.info(llm_response)
        # self.tts.text_to_speech(llm_response)

    def handle_user_input_from_text_interface(self, user_input: str) -> str:
        self.fill_slot(user_input)

        if self.is_done:
            return "LLM: Sending confirmation ..."

        self.history.add_human_message(user_input)
        self.logger.info(f"Handling user input '{user_input}' ...")
        prompt = self._generate_prompt(user_input)
        llm_response = self.llm_client.get_response(prompt=prompt)
        self.history.add_ai_message(llm_response)
        return llm_response

    def fill_slot(self, user_input: str) -> None:
        if "time" in self._next_slot.name:
            prompt = datetime_prompt(user_input)
            user_input = clean(
                string=self.llm_client.get_response(prompt=prompt),
            )
        self._next_slot.set_value(value=user_input)

    def get_user_input(self) -> str:
        if self.history.is_empty:
            initial_message = "I would like to create an appointment"
            self.history.add_human_message("")
            prompt = self._generate_prompt(initial_message)
            greetings_response = self.llm_client.get_response(
                prompt=prompt,
            )
            self.history.add_ai_message(greetings_response)
            return input(greetings_response + "\nUser: ")
        return input("User: ")

    def get_kwargs(self) -> dict:
        kwargs = {}
        for slot in self.slots:
            kwargs.update(slot.get_kwarg())
        return kwargs

    def run_text_interface(self):
        self.logger.info(f"All Slots: {self.slots}")
        while not self.is_done:
            user_input = self.get_user_input()
            self.logger.info(self.handle_user_input_from_text_interface(user_input))
        self.logger.info(f"All Slots: {self.slots}")
        self.logger.info(f"History: {self.history.get_history()}")
        self.logger.info(self.get_kwargs())


logger = utils.get_logger("SlotFiller")


def run_slot_filler():
    config = get_asr_llm_config()
    logger.info("%s: %s", config.__class__.__name__, json.dumps(config.__dict__, indent=2))

    slot_filler = SlotFillerSimple(
        func=CalendarAPI.create_new_appointment,
        llm_client=LLMClient(client=InferenceClient(model=config.llm_url)),
    )
    slot_filler.run_text_interface()


def clean(string: str) -> str:
    return string.replace("\n", "").replace("\t", "").replace(" ", "")


def datetime_prompt(user_input: str) -> str:
    now = datetime.datetime.now(datetime.UTC).isoformat()
    prompt_fmt = """
<s>[INST]
You specialise into converting spoken date and time into ISO 8601 formatted string output in UTC.
When you can't answer correctly, you simply answer "None"

Example:
input: today at 8 o'clock
now: 2024-06-01T18:56:15.900521+00:00
output: Given the current time "2024-06-01T18:56:15.900521+00:00" and the input "tomorrow at 8 o'clock pm", the ISO 8601 formatted string output in UTC would be: 2024-06-02T20:00:00+00:00

input: yesterday at 8 o'clock
now: 2024-06-01T18:56:15.900521+00:00
output: Given the current time "2024-06-01T18:56:15.900521+00:00" and the input "tomorrow at 8 o'clock pm", the ISO 8601 formatted string output in UTC would be: None

input: {user_input}
now: {now}
<</SYS>> [/INST]
output: Given the current time "{now}" and the input "{user_input}", the ISO 8601 formatted string output in UTC would be: 
"""
    return prompt_fmt.format(now=now, user_input=user_input)


if __name__ == "__main__":
    run_slot_filler()
