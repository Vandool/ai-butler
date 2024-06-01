import json
import logging
import os
from typing import Any

from sentence_transformers import SentenceTransformer, util

# Get the similarity model name from environment variable or use default
similarity_model_name = os.getenv("BUTLER_SIMILARITY_MODEL", "all-MiniLM-L6-v2")
model = SentenceTransformer(similarity_model_name)


def calculate_similarity(text1: str, text2: str) -> float:
    # Encode the texts into embeddings
    embeddings1 = model.encode(text1, convert_to_tensor=True)
    embeddings2 = model.encode(text2, convert_to_tensor=True)

    # Compute the cosine similarity between the embeddings
    similarity = util.pytorch_cos_sim(embeddings1, embeddings2)

    # The similarity is a 1x1 tensor, we get the value
    return similarity.item()


class CustomLogger(logging.Logger):
    def info_pretty(self, info: Any, indent: int = 2):
        self.info(json.dumps(info, indent=indent))

    def labeled_info_pretty(self, label: str, info: Any, indent: int = 2):
        self.info(f"{label}: {json.dumps(info, indent=indent)}")


def get_logger(module_name: str) -> CustomLogger:
    logging.setLoggerClass(CustomLogger)  # Set CustomLogger as the logger class
    logger = logging.getLogger(module_name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(asctime)s [%(name)s]: %(message)s", datefmt="%H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # You can change the log level globally using "LOG_LEVEL" env variable
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
        logger.propagate = False

    return logger
