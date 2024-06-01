from src.intent.intent_manager import CALENDAR, LECTURE, UNKNOWN
from src.intent.web_handler.calendar_api import CalendarAPI
from src.intent.web_handler.lecture_translator_api import LectureTranslatorApi

intent_map = {
    CALENDAR: CalendarAPI(),
    LECTURE: LectureTranslatorApi(),
    UNKNOWN: None,
}


def get_intent_class(intent):
    return intent_map[intent]
