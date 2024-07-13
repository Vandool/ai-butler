import functools
import logging
import sys
from http import HTTPStatus

from googleapiclient.errors import HttpError


def return_json(func):
    """Decorator to ensure the function returns data in JSON format."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        try:
            return response.json()
        except ValueError:
            logging.exception("Error in function '%s': Failed to decode JSON from response.", func.__name__)
            sys.exit(1)

    return wrapper


def check_status_code(func):
    """Decorator that checks the status code of an HTTP response and logs any errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        if response.status_code != HTTPStatus.OK:
            logging.exception(
                "Error in function '%s': HTTP Error %s: %s",
                func.__name__,
                response.status_code, 
                response.text,
            )
            sys.exit(1)
        return response

    return wrapper


def catch_http_exception(func):
    """Decorator that catches an HTTP exception and logs any errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        response = None
        try:
            response = func(*args, **kwargs)
        except HttpError as http_error:
            logging.exception(
                "Error in function '%s': HTTP Error %s: %s",
                func.__name__,
                http_error.status_code,
                http_error.error_details,
            )
        return response

    return wrapper
