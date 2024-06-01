from __future__ import annotations

import datetime
import inspect
import json
from collections.abc import Callable

from huggingface_hub import InferenceClient

from src import utils
from src.config.asr_llm_config import get_config
from src.history.history import History
from src.intent.intent import Slot
from src.intent.web_handler.calendar_api import CalendarAPI

logger = utils.get_logger("SlotFiller")

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


def extract_slots_from_function(func) -> list[Slot]:
    sig = inspect.signature(func)
    slots = []
    for param in sig.parameters.values():
        required = param.default is param.empty
        slots.append(Slot(name=param.name, param_type=param.annotation, is_required=required))
    return slots


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

    def __init__(self, func: Callable, llm_url: str):
        self.purpose: str = func.__name__
        self.slots: list[Slot] = extract_slots_from_function(func)
        self.client = InferenceClient(model=llm_url)
        self.history: History = History()
        self.is_greeting: bool = True

    @property
    def is_done(self) -> bool:
        return all(slot.is_set for slot in self.slots)

    @property
    def next_slot(self) -> Slot | None:
        for slot in self.slots:
            if not slot.is_set:
                return slot
        return None

    def generate_prompt(self, user_input: str) -> str:
        slot_instructions = self._SLOT_INSTRUCTION_FMT.format(name=self.next_slot.name)
        current_slots_str = self.next_slot.get_name_value()
        history_str = self.history.get_history()

        return self._DEFAULT_TEMPLATE_FMT.format(
            purpose=self.purpose,
            slot_instructions=slot_instructions,
            history=history_str,
            slots=current_slots_str,
            input=user_input,
        )

    def handle_user_input(self, user_input: str) -> str:
        self.fill_slot(user_input)

        if self.is_done:
            return "LLM: Sending confirmation ..."

        self.history.add_human_message(user_input)
        logger.info(f"Handling user input '{user_input}' ...")
        prompt = self.generate_prompt(user_input)
        response = self.generate_response(prompt)
        self.history.add_ai_message(response)
        return response

    def generate_response(self, prompt: str) -> str:
        return self.client.text_generation(
            prompt=prompt,
            max_new_tokens=128,
        )

    def get_user_input(self) -> str:
        if self.history.is_empty:
            initial_message = "I would like to create an appointment"
            self.history.add_human_message("")
            greetings = self.generate_response(prompt=self.generate_prompt(initial_message))
            self.history.add_ai_message(greetings)
            return input(greetings + "\nUser: ")
        return input("User: ")

    def fill_slot(self, user_input: str) -> None:
        if "time" in self.next_slot.name:
            user_input = clean(string=self.generate_response(prompt=datetime_prompt(user_input)))
        self.next_slot.set_value(value=user_input)

    def get_kwargs(self) -> dict:
        kwargs = {}
        for slot in self.slots:
            kwargs.update(slot.get_kwarg())
        return kwargs

    def run_text_interface(self):
        logger.info(f"All Slots: {self.slots}")
        while not self.is_done:
            user_input = self.get_user_input()
            logger.info(self.handle_user_input(user_input))
        logger.info(f"All Slots: {self.slots}")
        logger.info(f"History: {self.history.get_history()}")
        logger.info(self.get_kwargs())


def run_slot_filler():
    config = get_config()
    logger.info("%s: %s", config.__class__.__name__, json.dumps(config.__dict__, indent=2))

    slot_filler = SlotFillerSimple(func=CalendarAPI.create_new_appointment, llm_url=config.llm_url)
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
