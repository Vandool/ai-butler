import json

from src import utils
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.classifier.zero_shot_classifier import ZeroShotClassifier
from src.config.asr_llm_config import get_config
from src.intent.intent_manager import CALENDAR, LECTURE, IntentManager

logger = utils.get_logger("MyTextClient")


def test_classifiers():
    config = get_config()
    logger.info("%s: %s", config.__class__.__name__, json.dumps(config.__dict__, indent=2))

    intent_manager = IntentManager()
    intent_manager.add_intent(CALENDAR)
    intent_manager.add_intent(LECTURE)

    zero_shot_classifier = ZeroShotClassifier(model=config.zero_shot_model, intent_manager=intent_manager)

    few_shot_text_classifier = FewShotTextGenerationClassifier(llm_url=config.llm_url, intent_manager=intent_manager)

    while True:
        user_input = input("Enter your message (or type 'exit(e)' to quit(q)): ")
        if user_input.lower() in {"exit", "quit", "e", "q"}:
            break

        # intent_manager.use_unknown_intent = False
        # logger.info("ZeroShot=============")
        logger.info(f"{zero_shot_classifier.classify(user_input) =}")
        # logger.info(f"{zero_shot_classifier.classify_with_details(user_input) =}")
        # logger.info(f"{zero_shot_classifier.get_closest_intent(user_input) =}")
        logger.info(f"{few_shot_text_classifier.get_closest_intent_using_similarity(user_input) =}")
        # for prompt_type in PromptType:
        #     logger.info(f"FewShotTextGeneration============={prompt_type.name.upper()}")
        #     logger.info(f"{ few_shot_text_classifier.classify(user_input) =}")
        #     logger.info(f"{few_shot_text_classifier.classify_with_details(user_input, prompt_type=prompt_type) =}")
        #     logger.info(f"{few_shot_text_classifier.get_closest_intent(user_input, prompt_type=prompt_type) =}")
        #
        # intent_manager.use_unknown_intent = True
        # logger.info("ZeroShot=============")
        # logger.info(f"{zero_shot_classifier.classify(user_input) =}")
        # logger.info(f"{zero_shot_classifier.classify_with_details(user_input) =}")
        # logger.info(f"{zero_shot_classifier.get_closest_intent(user_input) =}")
        #
        # for prompt_type in PromptType:
        #     logger.info(f"FewShotTextGeneration============={prompt_type.name.upper()}")
        #     logger.info(f"{ few_shot_text_classifier.classify(user_input) =}")
        #     logger.info(f"{few_shot_text_classifier.classify_with_details(user_input, prompt_type=prompt_type) =}")
        #     logger.info(f"{few_shot_text_classifier.get_closest_intent(user_input, prompt_type=prompt_type) =}")


if __name__ == "__main__":
    test_classifiers()
