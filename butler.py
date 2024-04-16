import logging
import os
from huggingface_hub import InferenceClient

class Butler:
    def __init__(self, llm_url):
        self.history = "" # Initialize Conversation with empty string
        self.client = InferenceClient(model=llm_url)

    def process(self, new_message):
        print(new_message)
        
        # Process based on your dialog logic here

        # This is a simple bot that replies with a fun fact whenever you say fun

        if 'fun' in new_message.lower():
            print("Asking Llama for a fun fact")
            fun_fact = self.client.text_generation(prompt="<s>[INST] Hello, please tell me a fun fact about Germany in one short line? [/INST]", do_sample=True, max_new_tokens=64)
            print(fun_fact)