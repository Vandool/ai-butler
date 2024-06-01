from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Config:
    token: str  # Your personal token
    llm_url: str = "https://8cc9-141-3-25-29.ngrok-free.app"


def get_config() -> Config:
    return Config(
        llm_url=get_env_variable_with_default(var_name="BUTLER_LLM_URL", default=Config.llm_url),
        token=get_mandatory_env_variable("BUTLER_USER_TOKEN"),
    )


def get_mandatory_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        msg = "The environment variable '%s' is missing. Set the '%s' with appropriate value and re-run."
        raise OSError(msg, var_name, var_name)
    return value


def get_env_variable_with_default(var_name: str, default: str) -> str:
    return os.getenv(var_name, default)
