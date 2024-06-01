import json

import logger_utils
from src.arguments.config import get_config
from src.intent_classifier import Intent, IntentClassifier

logger = logger_utils.get_logger("MyTextClient")


def main():
    config = get_config()
    logger.info("%s: %s", config.__class__.__name__, json.dumps(config.__dict__, indent=2))

    classifier = IntentClassifier(llm_url=config.llm_url)
    classifier.intents = [
        Intent(
            name="Google Calendar Integration",
            examples=["Create an event", "Schedule a meeting", "What's my next event?"],
            description="This class deals with all the related activities around calendar events",
        ),
        Intent(
            name="Lecture Translator Integration",
            examples=[
                "Translate the lecture notes",
                "Convert the lecture audio to text",
                "What's the lecture summary?",
            ],
            description="This class deals with all the related activities around lecture notes, lecture summary and "
            "translations.",
        ),
    ]

    while True:
        user_input = input("Enter your message (or type 'exit(e)' to quit(q)): ")
        if user_input.lower() in {"exit", "quit", "e", "q"}:
            break
        classifier.classify(user_input)
        classifier.classify_intent(user_input)


if __name__ == "__main__":
    main()
