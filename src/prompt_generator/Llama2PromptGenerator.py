from __future__ import annotations

import os

from dotenv import load_dotenv
from huggingface_hub import HfFolder
from transformers import LlamaTokenizer

from src import utils
from src.intent.intent_manager import CALENDAR, LECTURE, IntentManager
from src.prompt_generator.prompt_generator import PromptType, create_or_list

load_dotenv()
access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN", default="<TOKEN>")

# Save the token to the Hugging Face cache
HfFolder.save_token(access_token)


class Llama2PromptGenerator:
    def __init__(self, intent_manager: IntentManager, num_shots: int = 1):
        self.intent_manager = intent_manager
        self.num_shots = num_shots
        self.tokenizer = LlamaTokenizer.from_pretrained(
            "meta-llama/Llama-2-7b-chat-hf",
            token=access_token,
        )
        self._validate_func_names()

    def generate_prompt(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
        """Generate a prompt based on the type specified."""
        return getattr(self, prompt_type.func_name)(input_text)

    def _generate_zero_shot_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt."""
        classes = create_or_list(self.intent_manager.list_intent_names())
        messages = [
            {"role": "system", "content": f"Classify the text into one of the following classes: {classes}"},
            {"role": "user", "content": f"{input_text} Class:"},
        ]
        return self.apply_chat_template(messages)

    def _generate_zero_shot_detailed_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt with class descriptions."""
        classes = "\n".join(f"{intent.name}: {intent.description}" for intent in self.intent_manager)
        messages = [
            {"role": "system", "content": f"Classify the text into one of the following classes:\n{classes}"},
            {"role": "user", "content": f"{input_text} Class:"},
        ]
        return self.apply_chat_template(messages)

    def _generate_one_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=1)

    def _generate_few_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        return self._generate_detailed_prompt(input_text, num_shots=3)

    def _generate_detailed_prompt(self, input_text: str, num_shots: int) -> str:
        """Generate a detailed classification prompt with descriptions and a specified number of examples."""
        examples = self.intent_manager.get_all_examples(num_shots=num_shots)
        classes = "\n".join(f"{intent.name}: {intent.description}" for intent in self.intent_manager)
        messages = [
            {"role": "system", "content": f"Classify the text into one of the following classes: {classes}\n"},
        ]

        for intent, ex_list in examples.items():
            for example in ex_list:
                messages.append({"role": "user", "content": f"Text: {example} Class:"})
                messages.append({"role": "assistant", "content": f"{intent}"})

        messages.append({"role": "user", "content": f"{input_text} Class:"})

        return self.apply_chat_template(messages)

    def _validate_func_names(self):
        for prompt_type in PromptType:
            if getattr(self, prompt_type.func_name) is None:
                err_msg = f"Llama2PromptGenerator should implement {prompt_type} with the exact name '{prompt_type.func_name}'."
                raise ValueError(err_msg)

    def apply_chat_template(self, messages):
        """Use Hugging Face's apply_chat_template method to format messages."""
        return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


if __name__ == "__main__":
    intent_manager = IntentManager()
    prompt_generator = Llama2PromptGenerator(intent_manager)
    intent_manager.add_intent(CALENDAR)
    intent_manager.add_intent(LECTURE)
    logger = utils.get_logger("Llama2PromptGenerator")

    input_text = "I would like to make an appointment"
    intent_manager.use_unknown_intent = True

    for p_type in PromptType:
        logger.info(f"---{p_type.name.upper()} Prompt---")
        logger.info(prompt_generator.generate_prompt(input_text=input_text, prompt_type=p_type))
        logger.info("")
