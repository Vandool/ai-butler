from huggingface_hub import InferenceClient

from src import utils
from src.asr.asr_module import ASRModule
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.config.asr_llm_config import get_asr_llm_config
from src.history.history import History
from src.intent.intent_manager import IntentManagerFactory
from src.llm_client.llm_client import LLMClient
from src.state.calendar_state import CalendarState
from src.state.state import State


class Butler:
    def __init__(self, history: History, llm_client: LLMClient, asr_module: ASRModule, states: list[State]) -> None:
        self.history = history
        self.llm_client = llm_client
        self.asr_module = asr_module
        self.logger = utils.get_logger(self.__class__.__name__)
        self.state: State = CalendarState(self.llm_client)
        self.states: list[State] = states

    def run(self):
        self.asr_module.run_session()


if __name__ == "__main__":
    args = get_asr_llm_config()
    llm_client = LLMClient(client=InferenceClient(args.llm_url))
    classifier = FewShotTextGenerationClassifier(
        llm_client=llm_client,
        intent_manager=IntentManagerFactory.get_intent_manager_with_unknown_intent(),
    )
    butler = Butler(
        history=History(),
        llm_client=llm_client,
        asr_module=ASRModule(args=args, classifier=classifier),
        states=[],
    )
    butler.run()
