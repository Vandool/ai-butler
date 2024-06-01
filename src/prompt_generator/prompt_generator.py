from __future__ import annotations

from src.intent.intent_manager import IntentManager


class PromptGenerator:
    def __init__(self, intent_manager: IntentManager, num_shots: int = 1):
        self.intent_manager = intent_manager
        self.num_shots = num_shots

    def generate_prompt(self, input_text: str, prompt_type: str = "simple") -> str:
        """Generate a prompt based on the type specified."""
        if prompt_type == "simple":
            return self._generate_simple_prompt(input_text)

        if prompt_type == "detailed":
            return self._generate_detailed_prompt(input_text)

        if prompt_type == "contextual":
            return self._generate_contextual_prompt(input_text)

        err_msg = f"Unknown prompt type: {prompt_type}"
        raise ValueError(err_msg)

    def _generate_simple_prompt(self, input_text: str) -> str:
        """Generate a simple classification prompt."""
        classes = " or ".join(self.intent_manager.list_intent_names())
        prompt = "<s>[INST] Classify the following text into one of the following classes: "
        prompt += f"{classes}.\nText: {input_text}\nClass: [/INST]</s>"
        return prompt

    def _generate_detailed_prompt(self, input_text: str) -> str:
        """Generate a detailed classification prompt with descriptions."""
        prompt = "<s>[INST] Classify the text into one of the following classes:\n"

        for intent in self.intent_manager:
            prompt += f"- {intent.name}: {intent.description}\n"

        prompt += f"\nText: {input_text}\nClass: [/INST]</s>"
        return prompt

    def _generate_contextual_prompt(self, input_text: str) -> str:
        """Generate a contextual classification prompt with examples."""
        intent_names = self.intent_manager.list_intent_names()
        if self.intent_manager.get_intent_length() == 2:
            classes = " or ".join(intent_names)
        else:
            classes = ", ".join(intent_names[:-1])
            classes = classes + f" or {intent_names[-1]}"

        prompt = "<s>[INST] As a professional text classifier, you can classify any given text into given classes.\n"
        prompt += "You only classify texts into 1 class and only use the name of class as answer.\n"

        class_helper = ""
        for i, intent in enumerate(self.intent_manager, start=1):
            class_helper += f"Class {i}:\n"
            class_helper += f"\tName: {intent.name}\n\tdescription: {intent.description}\n"

        prompt += (
            f"You know only {self.intent_manager.get_intent_length()} classes"
            f", which have the following names and descriptions.\n"
        )
        prompt += f"{class_helper}\n"
        prompt += "I show some examples of a text and a correct class\n"

        for intent, example_texts in self.intent_manager.get_all_examples(num_shots=self.num_shots).items():
            for example in example_texts:
                prompt += f"Text: {example}\nClass: {intent}\n\n"

        prompt += f"Please classify the text into one of the following classes: {classes}.\n\n"
        prompt += f"Text: {input_text}\nClass: [/INST]</s>"
        return prompt
