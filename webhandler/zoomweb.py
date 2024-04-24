import json
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webhandler import calender_quickstart, webutils


class ZoomHandler:
    def __init__(self, in_meeting=False, driver=None):
        self.in_meeting = in_meeting
        self.driver = driver
        self.handle = None

    def handle_command(self, command):
        '''
        Input: {"function":"controll_zoom","parameter":{"command":"join","link":"https://kit-lecture.zoom-x.de/j/61573381905?pwd=YkE3aUNYSnhXSnJnREMrV2VSMy85Zz09"}}', 'markup': 'command', 'session': '1182', 'sender': 'kitmeetingbutler:0', 'message_id': 2, 'num_subscribers': '1'}
        '''
        assert "function" in command  ## It should not be called otherwise or the format changed
        command_data = json.loads(command)

        if command_data["parameter"]["command"] == "join" and not self.in_meeting:
            try:
                self.in_meeting = True
                self.join_zoom(command_data["parameter"]["link"])
            except:
                self.in_meeting = False
                print("Meeting Ended, Couldn't join or terminated")


        if command_data["parameter"]["command"] == "end":
            if self.in_meeting:
                self.leave_zoom()

            else:
                try:
                    self.driver.switch_to.window(self.handle)
                    self.driver.close()
                except:
                    print("No opened browser")
            self.handle=None
            self.in_meeting = False
        print(command_data)

    def join_zoom(self, meeting_link):

        if meeting_link != "":

            meeting_id = meeting_link.split("/")[4].split("?")[0]
            pwd = meeting_link.split("/")[4].split("=")[1]


        else:
            meeting_id, pwd = calender_quickstart.get_zoom_details()
            if meeting_id == "":
                print("No meeting Available")
                assert 1==2
                return

        mlink_web = "https://app.zoom.us/wc/" + meeting_id + "/join?fromPWA=1&PWD=" + pwd
        js_code = f"window.open('{mlink_web}')"

        if self.handle == None:
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.execute_script(js_code)
            self.handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(self.handle)

        self.driver.get(mlink_web)

        time.sleep(5)
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("webclient")


        self.driver = webutils.click_id_button("onetrust-accept-btn-handler", self.driver)
        self.driver = webutils.click_id_button("wc_agree1", self.driver)


        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("webclient")

        self.driver = webutils.click_id_button("wc_agree1", self.driver)

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("webclient")

        time.sleep(5)
        self.driver = webutils.click_id_button("preview-audio-control-button", self.driver)
        self.driver = webutils.click_id_button("preview-video-control-button", self.driver)


        time.sleep(5)
        self.driver = webutils.enter_text("input-for-pwd", pwd, self.driver)
        self.driver = webutils.enter_text("input-for-name", "KIT-Meeting-Butler", self.driver, enter=True)

        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("webclient")


        while True:
            try:
                exit_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "leave-btn"))) # If it exists we are in waiting room, we need to keep waiting :)
            except:
                break

        time.sleep(5)

        self.in_meeting = True

        return


    def leave_zoom(self):

        self.driver.switch_to.window(self.handle)
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame("webclient")
        leave_button = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "zmu-btn.footer__leave-btn.ax-outline.ellipsis.zmu-btn--danger.zmu-btn__outline--blue")),
        )

        # Click the button
        leave_button.click()
        leave_button = WebDriverWait(self.driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "zmu-btn.leave-meeting-options__btn.leave-meeting-options__btn--default.leave-meeting-options__btn--danger.zmu-btn--default.zmu-btn__outline--white")),
        )

        # Click the button
        leave_button.click()


        cookies = self.driver.get_cookies()

        for cookie in cookies:
            if "zoom" in cookie["domain"]:
                self.driver.delete_cookie(cookie["name"])

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.handle = None

        self.in_meeting = False



    def toggle_mute(self):
        actions = ActionChains(self.driver)
        actions.key_down(Keys.ALT).send_keys("a").key_up(Keys.ALT).perform()
