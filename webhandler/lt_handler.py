import json
import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webhandler import webutils


class LTHandler:
    def __init__(self, driver=None, in_session=False):
        self.in_session = in_session
        self.driver = driver
        self.handle = None
        self.logged_in = False

    def handle_command(self, command):
        """
        Input: {
          "function": "controll_zoom",
          "parameter": {
            "command": "join",
            "link": "https://kit-lecture.zoom-x.de/j/61573381905?pwd=YkE3aUNYSnhXSnJnREMrV2VSMy85Zz09"
          },
          "markup": "command",
          "session": "1182",
          "sender": "kitmeetingbutler:0",
          "message_id": 2,
          "num_subscribers": "1"
        }
        """
        assert "function" in command  ## It should not be called otherwise or the format changed
        command_data = json.loads(command)

        if command_data["parameter"]["command"] == "start" and not self.in_session:
            try:
                self.in_session = True
                self.start_lt()
            except Exception as e:
                print("Session not created, terminated")
                print(str(e))
                self.in_session = False

        if command_data["parameter"]["command"] == "end":
            if self.in_session:
                self.end_lt()

            else:
                try:
                    self.driver.switch_to.window(self.handle)
                    self.driver.close()
                except:
                    logging.debug("No browser available")
            self.handle = None
            self.in_session = False
        logging.debug(command_data)

    def login_lt(self, username, pwd):
        if self.handle == None:
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.execute_script("""window.open("https://lt2srv-backup.iar.kit.edu/login","_blank");""")
            self.handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(self.handle)

        sign_in_buttons = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.dex-btn.theme-btn-provider")),
        )

        # Click the button
        sign_in_buttons[0].click()

        self.driver = webutils.enter_name_text("login", username, self.driver)
        self.driver = webutils.enter_name_text("password", pwd, self.driver)

        self.driver = webutils.click_id_button("submit-login", self.driver)

        redirect_url = self.driver.current_url

        self.logged_in = True

    def start_lt(self):
        if not self.logged_in:
            self.driver.get("https://lt2srv-backup.iar.kit.edu/index/live")

        else:
            self.driver.execute_script("""window.open("https://lt2srv-backup.iar.kit.edu/index/live","_blank");""")
            self.handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(self.handle)

        self.driver = webutils.click_id_button("start-lecture", self.driver)
        self.driver = webutils.click_id_button("legals", self.driver)
        self.driver = webutils.enter_text("name", "KIT-Meeting-Butler", self.driver)

        adv_options = self.driver.find_element(By.XPATH, "//button[contains(@onclick, 'toggleAdvancedOptions')]")
        adv_options.click()

        self.driver = webutils.click_id_button("logging", self.driver)

        start_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Start']")),
        )

        # Allow Microphone access
        start_button.click()

        self.in_session = True

    def end_lt(self):
        self.driver.switch_to.window(self.handle)
        self.driver = webutils.click_id_button("login", self.driver)  ## Bad Name, should ask to change
        alert = WebDriverWait(self.driver, 1).until(EC.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.accept()
        self.in_session = False
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.handle = None

    def list_clickable_buttons(self):
        """Lists all clickable buttons and button-like elements."""
        buttons = self.driver.find_elements(By.XPATH, "//button | //input[@type='button'] | //input[@type='submit']")

        clickable_elements = []
        for button in buttons:
            text = (
                button.text.strip()
                or button.get_attribute("value")
                or button.get_attribute("id")
                or button.get_attribute("name")
            )
            if text:
                clickable_elements.append(text)

        print("Available Clickable Buttons:")
        for button_text in clickable_elements:
            print(button_text)

        return clickable_elements


if __name__ == "__main__":
    import os

    driver = webutils.create_driver()
    driver.get("https://witeboard.com/")
    handler = LTHandler(driver=driver)
    handler.login_lt(
        username=os.environ.get("LT_USERNAME", ""),
        pwd=os.environ.get("LT_PASSWORD", ""),
    )
