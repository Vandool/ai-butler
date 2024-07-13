from __future__ import annotations

import os

from dotenv import load_dotenv
from huggingface_hub import HfFolder
from transformers import AutoTokenizer

from src.intent.intent_manager import IntentManager
from src.prompt_generator.prompt_generator import PromptType, create_or_list

load_dotenv()
access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN", default="<TOKEN>")
chat_template_model = os.getenv("HUGGINGFACE_CHAT_TEMPLATE_MODEL", default="meta-llama/Meta-Llama-3-8B-Instruct")

# Save the token to the Hugging Face cache
HfFolder.save_token(access_token)


class Llama3PromptGenerator:
    def __init__(self, intent_manager: IntentManager | None = None, num_shots: int = 1):
        self.intent_manager = intent_manager
        self.num_shots = num_shots
        self.tokenizer = AutoTokenizer.from_pretrained(
            chat_template_model,
            token=access_token,
        )
        self._validate_func_names()
        if intent_manager and len(intent_manager.list_intent_names()) > 1:
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
        return self.apply_chat_template(messages)

    def _generate_zero_shot_detailed_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt with class descriptions."""
        messages = [
            {"role": "system", "content": "Classify the text into one of the following classes:"},
            {"role": "user", "content": f"{input_text}"},
        ]
        return self.apply_chat_template(messages)

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

        return self.apply_chat_template(messages)

    def _validate_func_names(self):
        for prompt_type in PromptType:
            if getattr(self, prompt_type.func_name) is None:
                err_msg = f"Llama2PromptGenerator should implement {prompt_type} with the exact name '{prompt_type.func_name}'."
                raise ValueError(err_msg)

    def apply_chat_template(self, messages):
        """Use Hugging Face's apply_chat_template method to format messages."""
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
