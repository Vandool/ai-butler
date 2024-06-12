import functools
import inspect
import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Final


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

def decorator_test(func):
    """Decorator that checks the status code of an HTTP response and logs any errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        print(response)
        return response

    return wrapper

class TestObjCall:
    def __init__(self):
        self.c = "c"

    @staticmethod
    @decorator_test
    def func_a(a: str):
        return f"a = {a}"

    def func_b(self, a: str, b: str) -> str:
        return f"{a} = {b} = {self.c}"

    def func_c(self, a: str, b: str, c: str) -> str:
        return f"{a} = {b} = {c} = {self.c}"

    def func_d(self, a: str, b: str, c: str, d: str) -> str:
        return f"{a} = {b} = {c} = {self.c} = {d}"
