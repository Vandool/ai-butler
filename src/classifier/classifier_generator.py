from src import utils
from src.classifier.base_classifier import FunctionCallClassifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.intent.intent import Intent
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient


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
    module: object,
    llm_client: LLMClient,
    *,
    use_unknown: bool = True,
):
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
    return FunctionCallClassifier(
        llm_client=llm_client,
        intent_manager=intent_manager_,
        module=module,
    )
