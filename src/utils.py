import inspect
import json
import logging
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

import pytz


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


logger = get_logger("UTILS")

_IS_MARKED_ATTR: Final[str] = "_is_marked"


def mark_intent(func: Callable) -> Callable:
    setattr(func, _IS_MARKED_ATTR, True)
    return func


@dataclass
class FunctionInfo:
    name: str
    has_slots: bool
    docstring: str


def get_marked_functions_and_docstrings(module: object) -> dict[str, FunctionInfo]:
    functions_info = {}
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and getattr(obj, _IS_MARKED_ATTR, False):
            function_info = FunctionInfo(
                name=name,
                has_slots=bool(inspect.signature(obj).parameters),
                docstring=inspect.getdoc(obj),
            )
            functions_info[name] = function_info
    return functions_info


def parse_docstring(docstring) -> (str, list[str]):
    lines = docstring.strip().split("\n")
    description = lines[0].strip()

    examples = []
    examples_start = False
    for line in lines[1:]:
        if "Examples:" in line:
            examples_start = True
        elif examples_start:
            example = line.strip()
            if example.startswith("- "):
                examples.append(example[2:].strip())

    return description, examples



def extract_json(text: str) -> dict[str, Any]:
    """
    :raises: json.JSONDecodeError
    :raises: ValeError
    """
    return json.loads(extract_first_curly(text))


def escape_all_inner_quotes(json_str: str) -> str:
    def replace_inner_quotes(match):
        # Only replace inner quotes within the value of a key-value pair
        value = match.group(0)
        return value.replace('"', '\\"')

    # Regex to find all values within quotes
    pattern = r'(?<=": ")[^"]*(?=")'

    escaped_str = re.sub(pattern, replace_inner_quotes, json_str)
    return escaped_str


def extract_first_curly(text: str) -> str:
    # Regular expression to match content within braces including the braces
    pattern = re.compile(r"\{[^}]*\}")

    # Search for the first occurrence of the pattern in the input string
    match = pattern.search(text)

    # Extract and print the matched string
    if match:
        return match.group()

    raise ValueError("No curly brackets found in text")


@dataclass
class FunctionCall:
    function_name: str
    parameters: list[str]


def parse_function_call(text: str) -> FunctionCall:
    first_split = text.split("(")
    function_name = first_split[0].strip()
    params_str = [s.strip().replace('"', "").replace("'", "") for s in first_split[1].strip(")").split(",")]

    return FunctionCall(function_name=function_name, parameters=params_str)


def get_function_def(function: Callable) -> str:
    source_code = inspect.getsource(function)
    def_index = source_code.find("def ")
    if def_index == -1:
        err_msg = "Function definition not found in the source code"
        raise ValueError(err_msg)

    # Remove the examples and the actual function implementation
    source_code = source_code[def_index:]

    return f"{source_code.split('Examples')[0].strip()}\n\"\"\"\n    pass\n"


def get_candidates(module: object) -> str:
    return [
        get_function_def(obj)
        for _, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and getattr(obj, _IS_MARKED_ATTR, False)
    ]


def ensure_iso_8601_format(date_str: str) -> str:
    berlin_tz = pytz.timezone("Europe/Berlin")
    try:
        # Try to parse the string to a datetime object in the correct format
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
        # Convert to Berlin time
        dt = dt.astimezone(berlin_tz)
        return dt.isoformat()
    except ValueError:
        # If parsing fails, try to convert the string to the correct format
        try:
            # Attempt to parse the string with a common format
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
            # Convert to Berlin time
            dt = dt.astimezone(berlin_tz)
            return dt.isoformat()
        except ValueError:
            raise ValueError("The provided date string is not in a recognizable format.")


def get_now_tz_berlin() -> datetime:
    return datetime.now(tz=pytz.timezone("Europe/Berlin"))


