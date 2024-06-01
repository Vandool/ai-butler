from __future__ import annotations

import json
from dataclasses import dataclass

from huggingface_hub import InferenceClient
from transformers import pipeline

import logger_utils


@dataclass
class Intent:
    name: str
    examples: list[str]
    description: str | None = None


class IntentClassifier:
    def __init__(self, llm_url: str, num_shots: int = 1):
        self.client = InferenceClient(model=llm_url)
        self.num_shots = num_shots
        self.logger = logger_utils.get_logger(self.__class__.__name__)
        self._intents: list[Intent] | None = None
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    def classify(self, text: str) -> list[Intent]:
        # Perform classification using the Zero-shot-Classifier as baseline
        response = self.classifier(text, [intent.name for intent in self.intents])
        self.logger.debug(f"Zero-shot-Classifier response:\n{response}")  # noqa: G004
        return response

    def classify_intent(self, input_text: str) -> str:
        candidate_labels = [intent.name for intent in self.intents]
        self.logger.debug("candidate_labels: %s", str(candidate_labels))

        examples = {intent.name: intent.examples[: self.num_shots] for intent in self.intents}
        self.logger.debug("intent examples: %s", str(examples))

        # Generate a prompt
        prompt = self._generate_prompt(input_text, examples)
        self.logger.debug("prompt: %s\n\n", prompt)

        # Perform classification using the InferenceClient
        response = self.client.text_generation(
            prompt=prompt,
            details=True,
            max_new_tokens=max([len(c) for c in candidate_labels]),
        )
        self.logger.debug("Client Response:\n%s", response.generated_text)
        self.logger.debug("Client Response Details:\n%s", json.dumps(vars(response), indent=4))
        return response

    def _generate_prompt(self, input_text: str, examples: dict) -> str:
        """Generate a prompt for the given input text.

        Meaning of the used symbols
            <s> and </s>: Marks the start and end of the sequence.
            [INST] and [/INST]: Indicate the instruction or task.
        """
        if len(self.intents) == 2:
            classes = " or ".join([intent.name for intent in self.intents])
        else:
            classes = ", ".join([intent.name for intent in self.intents[: len(self.intents) - 1]])
            classes = classes + f" or {self.intents[-1].name}"
        prompt = "<s>[INST] As a professional text classifier, you can classify any given text into given classes.\n"
        prompt += "You only classify texts into 1 class and only use the name of class as answer.\n"

        class_helper = ""
        for i, intent in enumerate(self.intents, start=1):
            class_helper += f"Class {1}:\n"
            class_helper += f"\tName: {intent.name}\ndescription: {intent.description}\n"
        prompt += f"You know only {len(self.intents)} classes, which have the following names and description.\n"
        prompt += f"{class_helper}\n"
        prompt += "I show some examples of a text and a correct class\n"

        for intent, example_texts in examples.items():
            for example in example_texts:
                prompt += f"Text: {example}\nClass: {intent}\n\n"

        prompt += f"Please classify the text into one of the following classes: {classes}.\n\n"
        prompt += f"Text: {input_text}\nClass: [/INST]</s>"
        return prompt

    @property
    def intents(self) -> list[Intent]:
        return self._intents

    @intents.setter
    def intents(self, intents: list[Intent]) -> None:
        # Assertion for test
        assert len(intents) > 1
        self._intents = intents
