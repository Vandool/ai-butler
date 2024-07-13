from __future__ import annotations

import webbrowser

from src import utils

logger = utils.get_logger("LectureAPI")


class LectureTranslatorAPI:
    def __init__(self):
        super().__init__()

    @staticmethod
    def open_html_link(response: dict) -> None:
        if link := response.get("htmlLink"):
            # Open the link in the default web browser
            webbrowser.open(link)

    # TODO: add real API call
    @staticmethod
    @utils.mark_intent
    def get_lecture_content():
        """Get content of the lecture.

        Examples:
            - I'd like to summarize the last lecture.
            - Please give me the content of the last lecture.
            - Can you give me the content of the last lecture?
        """
        f = open("C:\\Users\\namid\\PycharmProjects\\NLP_practical\\lecture.txt")
        lecture_content = f.read()
        return lecture_content


if __name__ == "__main__":
    lecture_api = LectureTranslatorAPI()
    print(lecture_api.get_lecture_content())
    # link = "https://lt2srv-backup.iar.kit.edu/archivesession/%252F%252Fhome%252Fadmin%2540example.com%252FLecture"
    # r = requests.get(link)
    # print(r.text)

# do something else


# lectureTranslatorApi = LectureTranslatorApi()
# lectureTranslatorApi.login_lt("utzpi", "123")
