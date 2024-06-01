import os


def get_mandatory_env_variable(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        msg = "The environment variable '%s' is missing. Set the '%s' with appropriate value and re-run."
        raise OSError(msg, var_name, var_name)
    return value


def get_env_variable_with_default(var_name: str, default: str) -> str:
    return os.getenv(var_name, default)
