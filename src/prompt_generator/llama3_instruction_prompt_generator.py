from __future__ import annotations

import datetime
import os
from typing import ClassVar

import pytz
from dotenv import load_dotenv
from huggingface_hub import HfFolder, InferenceClient
from transformers import AutoTokenizer

from src import utils
from src.config.asr_llm_config import get_asr_llm_config
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient
from src.prompt_generator.prompt_generator import PromptType, create_or_list
from src.web_handler.calendar_api import CalendarAPI

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


class Llama3InstructPromptGenerator:
    def __init__(self, intent_manager: IntentManager, num_shots: int = 1):
        self.intent_manager = intent_manager
        self.num_shots = num_shots
        self.chat_template_generator = ChatTemplateGenerator(
            chat_template_model=chat_template_model,
            access_token=access_token,
        )
        self._validate_func_names()
        self.classes = create_or_list(self.intent_manager.list_intent_names())
        self.classes_detailed = str({intent.name: intent.description for intent in self.intent_manager})

    def generate_prompt(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
        """Generate a prompt based on the type specified."""
        return getattr(self, prompt_type.func_name)(input_text)

    def _generate_zero_shot_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt."""
        messages = [
            {"role": "system", "content": f"Classify the text into one of the following classes: {self.classes}"},
            {"role": "user", "content": input_text},
        ]
        return self.chat_template_generator.apply_chat_template(messages)

    def _generate_zero_shot_detailed_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt with class descriptions."""
        messages = [
            {"role": "system", "content": "Classify the text into one of the following classes:"},
            {"role": "user", "content": f"{input_text} Class:"},
        ]
        return self.chat_template_generator.apply_chat_template(messages)

    def _generate_one_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=1, is_detailed=True)

    def _generate_one_shot_per_class_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=1)

    def _generate_few_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=3, is_detailed=True)

    def _generate_few_shot_per_class_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=3)

    def _generate_detailed_prompt(self, input_text: str, num_shots: int, *, is_detailed: bool = False) -> str:
        """Generate a detailed classification prompt with descriptions and a specified number of examples."""
        examples = self.intent_manager.get_all_examples(num_shots=num_shots)
        messages = [
            {
                "role": "system",
                "content": f"You are chatbot helping the user to complete his tasks. "
                f"Classify the text into one of the following classes: "
                f"{self.classes_detailed if is_detailed else self.classes}",
            },
        ]

        for intent, ex_list in examples.items():
            for example in ex_list:
                messages.append({"role": "user", "content": example})
                messages.append({"role": "assistant", "content": intent})

        messages.append({"role": "user", "content": input_text})

        return self.chat_template_generator.apply_chat_template(messages)

    def _validate_func_names(self):
        for prompt_type in PromptType:
            if getattr(self, prompt_type.func_name) is None:
                err_msg = f"Llama2PromptGenerator should implement {prompt_type} with the exact name '{prompt_type.func_name}'."
                raise ValueError(err_msg)


class Llama3InstructFunctionCallPromptGenerator:
    _SYS_PROMPT_FMT: ClassVar[str] = (
        "Below, you are presented with {n_candidates} candidate functions. Your task is to analyze a specific user input to "
        "determine which of these functions most appropriately addresses the query. Then, construct the correct function"
        " call with all necessary parameters, adhering to proper syntax. "
        "Format for function call: function_name(param1, param2, ...) "
        "Candidate Functions: \n"
        "{candidates}"
        "def irrelevant_function(): ”’If user query is not related to any of the predefined functions, this function will be called. Args: Returns: if the user asks a questiong about the history of the conversation, the question will be answered”’"
        "For time reference:"
        "Now: {now} "
        "You always reply with the following format:"
        '{{"text": "<your textual response>", "function_call": "<the function call>"}}'
        "You only reply with the above format and nothing else"
        "Your goal is to select the most suitable function out of the n_candidates candidates and generate an accurate function call that directly addresses the user's last input or the previous ones, if they are 100% related. Ensure the output is a syntactically valid function call. If the user asks a question about the history of your conversation, you can answer it based on the history."
    )
    q = "I would like to set a meeting for meeting my supervisor in 2 days at his office to discuss my final presentation. I think he should be free from ten till eleven in the morning"
    one_func = """
    def create_new_appointment(summary: str, start_time: str, end_time: str, description: str | None = None, location: str | None = None,): ”’Create a new appointment in the calendar using the specified parameters. Parameters: - summary (str): A brief description of the appointment. - start_time (str): The start time of the appointment in ISO 8601 format. - end_time (str): The end time of the appointment in ISO 8601 format. - description (str, optional): Additional details about the appointment. Default is None. - location (str, optional): The location where the appointment will take place. Default is None.”’ 
    """

    def __init__(self, module: object | None = None):
        self.candidates = utils.get_candidates(module)
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

    def get_default_chat_messages(
        self,
        user_input: str,
        candidates: list[str],
        extend_messages: list[dict] | None = None,
        num_shots: int = 0,
    ):
        # Get the current time in UTC
        now_utc = datetime.datetime.now(datetime.UTC)

        # Convert UTC time to Berlin time
        berlin_tz = pytz.timezone("Europe/Berlin")
        now = now_utc.astimezone(berlin_tz)
        # Round down to the nearest hour
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
        shots = (
            [
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
                    "content": f'{{"text": "Okey, can you tell me when should it end?", "function_call": "create_new_appointment(\'Appointment\', {next_week_10.isoformat()!s}, None)"}}',
                },
                {
                    "role": "user",
                    "content": "What is the timezone of my calendar?",
                },
                {
                    "role": "assistant",
                    "content": '{"text": "I assume the timezone should be by default your local timezone", "function_call": "irrelevant_function()"}',
                },
            ],
        )

        messages = [
            {
                "role": "system",
                "content": self._SYS_PROMPT_FMT.format(
                    now=now.isoformat(),
                    n_candidates=len(candidates) + 1,
                    candidates="\n".join(candidates),
                ),
            },
        ]

        messages.extend(*shots[:num_shots])

        if extend_messages:
            messages.extend(extend_messages)

        messages.append(
            {
                "role": "user",
                "content": f"{user_input}",
            },
        )
        return messages


if __name__ == "__main__":
    # # Llama3InstructPromptGenerator
    # intent_manager = IntentManager()
    # intent_manager.add_intent(CALENDAR)
    # intent_manager.add_intent(LECTURE)
    # intent_manager.use_unknown_intent = True
    # prompt_generator = Llama3InstructPromptGenerator(intent_manager)
    # logger = utils.get_logger("Llama2PromptGenerator")
    #
    # input_text = "I would like to make an appointment"
    #
    # for p_type in PromptType:
    #     logger.info(f"---{p_type.name.upper()} Prompt---")
    #     logger.info(prompt_generator.generate_prompt(input_text=input_text, prompt_type=p_type))
    #     logger.info("")
    #
    # Llama3InstructPromptGeneratorFunctionCall
    args = get_asr_llm_config()
    llm_client = LLMClient(client=InferenceClient(args.llm_url))

    generator = Llama3InstructFunctionCallPromptGenerator(module=CalendarAPI)

    prompt = generator.generate_prompt(
        input_text="I would like to set a meeting for meeting my supervisor in 2 days at his office to discuss my final presentation. I think he should be free from ten till eleven in the morning",
        prompt_type=PromptType.FEW_SHOT_DETAILED,
    )
    print(prompt)
    print("------------------")

    response = llm_client.get_response(
        prompt=prompt,
        max_new_tokens=128,
    )
    print(response)
    print("------------------")

    prompt = generator.generate_prompt(
        input_text="I would like to set a meeting for meeting my supervisor in 2 days at his office to discuss my final presentation. I think he should be at ten in the morning",
        prompt_type=PromptType.FEW_SHOT_DETAILED,
    )
    print(prompt)
    print("------------------")

    response = llm_client.get_response(
        prompt=prompt,
        max_new_tokens=128,
    )
    print(response)
    print("------------------")
