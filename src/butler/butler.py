from huggingface_hub import InferenceClient

from src import utils
from src.asr.asr_module import ASRModule


class Butler:
    def __init__(self, llm_url: str, asr_module: ASRModule) -> None:
        self.history = ""  # Initialize Conversation with empty string
        self.client = InferenceClient(model=llm_url)
        self.logger = utils.get_logger(self.__class__.__name__)
        self.asr_module: ASRModule = asr_module

    def process(self, new_message, max_new_tokens=64):
        self.logger.info(new_message)

        # Process based on your dialog logic here

        # This is a simple bot that replies with a fun fact whenever you say fun

        if "ok butler" in new_message.lower():
            self.logger.info("Asking Llama for a fun fact")
            response = self.client.text_generation(
                prompt="<s>[INST] Hello, please tell me a fun fact about Germany in one short line? [/INST]",
                do_sample=True,
                max_new_tokens=max_new_tokens,
            )
            self.logger.info(response)
