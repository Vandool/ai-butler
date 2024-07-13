from __future__ import annotations

from src import utils
from src.classifier.base_classifier import FunctionCallClassifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient
from src.prompt_generator.llama3_instruction_prompt_generator import get_prompt_generator
from src.web_handler.calendar_api import CalendarAPI
from src.web_handler.lecture_translator_api import LectureTranslatorAPI


def generate_classifier(
    module: object,
    llm_client: LLMClient,
    *,
    use_unknown: bool = True,
) -> FewShotTextGenerationClassifier:
    intent_manager_ = IntentManager()
    for func_info in utils.get_marked_functions_and_docstrings(module=module).values():
        description, examples = utils.parse_docstring(func_info.docstring)
        intent_manager_.add_intent(
            Intent(
                name=func_info.name,
                description=description,
                examples=examples,
            ),
        )
        intent_manager_.use_unknown_intent = use_unknown
    return FewShotTextGenerationClassifier(
        llm_client=llm_client,
        intent_manager=intent_manager_,
    )


def generate_function_caller_classifier(
    api: CalendarAPI | LectureTranslatorAPI | None,
    llm_client: LLMClient,
    *,
    use_unknown: bool = True,
):
    intent_manager_ = IntentManager()
    if api is not None:
        for func_info in utils.get_marked_functions_and_docstrings(module=api).values():
            description, examples = utils.parse_docstring(func_info.docstring)
            intent_manager_.add_intent(
                Intent(
                    name=func_info.name,
                    description=description,
                    examples=examples,
                ),
            )
        intent_manager_.use_unknown_intent = use_unknown

    return FunctionCallClassifier(
        llm_client=llm_client,
        intent_manager=intent_manager_,
        prompt_generator=get_prompt_generator(api=api),
    )
