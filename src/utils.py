import logging
import os

from sentence_transformers import SentenceTransformer, util

# Load a pre-trained model from sentence-transformers
model = SentenceTransformer("all-MiniLM-L6-v2")


def calculate_similarity(text1: str, text2: str) -> float:
    # Encode the texts into embeddings
    embeddings1 = model.encode(text1, convert_to_tensor=True)
    embeddings2 = model.encode(text2, convert_to_tensor=True)

    # Compute the cosine similarity between the embeddings
    similarity = util.pytorch_cos_sim(embeddings1, embeddings2)

    # The similarity is a 1x1 tensor, we get the value
    return similarity.item()


def get_logger(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s [%(name)s]: %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # You can change the log level globally using "LOG_LEVEL" env variable
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    logger.propagate = False
    return logger
