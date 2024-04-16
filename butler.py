import logging
import os
from huggingface_hub import InferenceClient

class Butler:
    def __init__(self, llm_url):
        self.history = "" # Initialize Conversation with empty string
        self.client = InferenceClient(model=llm_url)

    def process(self, new_message):
        logging.info("Recieved New Message from ASR:\n " + new_message)
        
