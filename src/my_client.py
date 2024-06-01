import os
from dataclasses import dataclass

from src.intent_classifier import Intent, IntentClassifier


@dataclass
class Args:
    llm_url: str
    token: str


def get_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        msg = "The environment variable %s is missing."
        raise OSError(msg, var_name)
    return value


def get_args() -> Args:
    return Args(llm_url=get_env_variable("BUTLER_LLM_URL"), token=get_env_variable("BUTLER_USER_TOKEN"))


def main():
    args = get_args()
    classifier = IntentClassifier(llm_url=args.llm_url)
    classifier.intents = [
        Intent(
            name="Google Calendar Integration",
            examples=["Create an event", "Schedule a meeting", "What's my next event?"],
        ),
        Intent(
            name="Lecture Translator Integration",
            examples=[
                "Translate the lecture notes",
                "Convert the lecture audio to text",
                "What's the lecture summary?",
            ],
        ),
    ]

    while True:
        user_input = input("Enter your message (or type 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit"]:
            break
        classifier.classify(user_input)
        classifier.classify_intent(user_input)


if __name__ == "__main__":
    main()
