import functools
import logging
import sys
from http import HTTPStatus

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def create_driver():
    # Replace 'path_to_webdriver' with the path to your webdriver executable
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=BlockCredentialedSubresources")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "profile.default_content_setting_values.notifications": 1,
        },
    )
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "credentials_enable_service": False,
            "profile.password_maanager_enabled": False,
        },
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(
        service=ChromeService(executable_path="/home/titanic/butler/chromedriver"),
        options=options,
    )

    return driver


def click_id_button(name, driver):
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, name)))
    button.click()
    return driver


def click_name_button(name, driver):
    button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, name)))
    button.click()
    return driver


def enter_text(name, text, driver, enter=False):
    box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, name)))
    box.clear()
    box.send_keys(text)
    if enter:
        box.send_keys(Keys.ENTER)
    return driver


def enter_name_text(name, text, driver, enter=False):
    box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, name)))
    box.clear()
    box.send_keys(text)
    if enter:
        box.send_keys(Keys.ENTER)
    return driver


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
                "Error in function '%s': HTTP Error %s: %s", func.__name__, response.status_code, response.text
            )
            sys.exit(1)
        return response

    return wrapper
