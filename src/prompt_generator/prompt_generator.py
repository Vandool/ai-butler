from __future__ import annotations

import enum

from src import utils
from src.intent.intent import CALENDAR, LECTURE
from src.intent.intent_manager import IntentManager


class PromptType(enum.Enum):
    ZERO_SHOT = "zero_shot", "_generate_zero_shot_prompt"
    ZERO_SHOT_DETAILED = "zero_shot_detailed", "_generate_zero_shot_detailed_prompt"
    ONE_SHOT_PER_CLASS_DETAILED = "one_shot_per_class_detailed", "_generate_one_shot_per_class_detailed_prompt"
    FEW_SHOT_DETAILED = "few_shot_per_class_detailed", "_generate_few_shot_per_class_detailed_prompt"

    @property
    def name(self):
        return self.value[0]

    @property
    def func_name(self):
        return self.value[1]


class PromptGenerator:
    def __init__(self, intent_manager: IntentManager, num_shots: int = 1):
        self.intent_manager = intent_manager
        self.num_shots = num_shots
        self._validate_func_names()

    def generate_prompt(self, input_text: str, prompt_type: PromptType = PromptType.ZERO_SHOT) -> str:
        """Generate a prompt based on the type specified."""
        return getattr(self, prompt_type.func_name)(input_text)

    def _generate_zero_shot_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt."""
        classes = create_or_list(self.intent_manager.list_intent_names())
        prompt = f"<s>[INST] Classify the text into one of the following classes: {classes}.\n"
        prompt += f"Text: {input_text} [/INST]</s> \nClass: "
        return prompt

    def _generate_zero_shot_detailed_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt with class descriptions."""
        classes = create_or_list(self.intent_manager.list_intent_names())
        prompt = "<s>[INST] Classify the text into one of the following classes:\n"

        for intent in self.intent_manager:
            prompt += f"- {intent.name}: {intent.description}\n"

        prompt += f"Text: {input_text} [/INST]</s> \nClass: "
        return prompt

    def _generate_one_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        """Generate a detailed classification prompt with descriptions and one example."""
        prompt = "<s>[INST] Classify the text into one of the following classes:\n"

        for intent in self.intent_manager:
            prompt += f"- {intent.name}: {intent.description}\n"

        prompt += "\nHere is an example:\n"
        example_texts = self.intent_manager.get_all_examples(num_shots=1)
        for intent, examples in example_texts.items():
            example = examples[0]  # Using the first example for one-shot
            prompt += f"Text: {example}\nClass: {intent}\n"

        prompt += f"\nNow classify the following text:\nText: {input_text} [/INST]</s> \nClass: "
        return prompt

    def _generate_few_shot_per_class_detailed_prompt(self, input_text: str) -> str:
        """Generate a detailed classification prompt with descriptions and three examples."""
        prompt = "<s>[INST] Classify the text into one of the following classes:\n"

        for intent in self.intent_manager:
            prompt += f"- {intent.name}: {intent.description}\n"

        prompt += "\nHere are some examples:\n"
        example_texts = self.intent_manager.get_all_examples(num_shots=3)
        for intent, examples in example_texts.items():
            for example in examples:
                prompt += f"Text: {example}\nClass: {intent}\n"

        prompt += f"\nNow classify the following text:\nText: {input_text} [/INST]</s>\nClass:"
        return prompt

    def _validate_func_names(self):
        for prompt_type in PromptType:
            if getattr(self, prompt_type.func_name) is None:
                err_msg = (
                    f"PromptGenerator should implement {prompt_type} with the exact name '{prompt_type.func_name}'."
                )
                raise ValueError(err_msg)


def create_or_list(items: list[str]) -> str:
    assert len(items) > 1  # Assertion should be deleted later
    return ", ".join(items[:-1]) + ", or " + items[-1]


if __name__ == "__main__":
    intent_manager = IntentManager()
    prompt_generator = PromptGenerator(intent_manager)
    intent_manager.add_intent(CALENDAR)
    intent_manager.add_intent(LECTURE)
    logger = utils.get_logger("PromptGenerator")

    input_text = "A text to be classified"

    for p_type in PromptType:
        logger.info(f"---{p_type.name.upper()} Prompt---")
        logger.info(prompt_generator.generate_prompt(input_text=input_text, prompt_type=p_type))
        logger.info("")

    intent_manager.use_unknown_intent = True
    for p_type in PromptType:
        logger.info(f"---{p_type.name.upper()} Prompt---")
        logger.info(prompt_generator.generate_prompt(input_text=input_text, prompt_type=p_type))
        logger.info("")
