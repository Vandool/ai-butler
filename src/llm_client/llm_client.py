import json

from huggingface_hub import InferenceClient

from src import utils
from src.config.asr_llm_config import get_asr_llm_config


class LLMClient:
    def __init__(self, client: InferenceClient):
        self.client = client
        self.logger = utils.get_logger(self.__class__.__name__)

    def get_response(self, prompt: str, max_new_tokens: int = 128) -> str:
        generated_text = self.client.text_generation(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
        )
        self.logger.debug("Client generated texts:\n%s", generated_text)
        return generated_text

    def get_detailed_response(self, prompt: str, max_new_tokens: int = 128) -> dict:
        detailed_response = json.dumps(
            vars(
                self.client.text_generation(
                    prompt=prompt,
                    max_new_tokens=max_new_tokens,
                    details=True,
                ),
            ),
        )
        self.logger.debug("Client generated texts details:\n%s", detailed_response)
        return detailed_response


if __name__ == "__main__":
    args = get_asr_llm_config()
    llm_client = LLMClient(client=InferenceClient(args.llm_url))
    print(type(llm_client.get_response(prompt="hi")))
    response = llm_client.get_detailed_response(prompt="hi")
    print(type(response))
