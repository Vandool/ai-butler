from __future__ import annotations

import datetime
import json
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src import utils
from src.classifier.zero_shot_classifier import ZeroShotClassifier
from src.config import google_api_config
from src.config.asr_llm_config import AsrLlmConfig
from src.config.google_api_config import GoogleApiConfig
from src.intent import intent
from src.intent.intent_manager import IntentManager
from src.intent.processable import Processable
from src.intent.web_handler.my_web_utils import catch_http_exception

# Authentication and service creation
SCOPES = ["https://www.googleapis.com/auth/calendar"]

gc_config = google_api_config.get_google_api_config()


@catch_http_exception
def build_service(config: GoogleApiConfig) -> Any:
    creds = service_account.Credentials.from_service_account_info(
        google_api_config.get_service_account_info(config=config),
        scopes=SCOPES,
    )
    if creds and not creds.valid:
        return build("calendar", "v3", credentials=creds)
    err_msg = "Google API credentials not valid"
    raise Exception(err_msg)  # noqa: TRY002


service = build_service(config=gc_config)
logger = utils.get_logger("CalendarAPI")


def get_classifier():
    intent_manager_ = IntentManager()
    for name_, docstring_ in intent.get_marked_functions_and_docstrings(module=CalendarAPI).items():
        intent_manager_.add_intent(
            intent.Intent(
                name=name_,
                description=docstring_,
            ),
        )
    return ZeroShotClassifier(model=AsrLlmConfig.zero_shot_model, intent_manager=intent_manager_)


class CalendarAPI(Processable):
    def __init__(self):
        super().__init__()
        self.classifier = get_classifier()

    def process(self, the_input: str) -> Any:
        logger.info(f"Processing '{the_input}'")
        logger.info(f"Intent found: {self.classifier.get_closest_intent(the_input)}")

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def create_new_appointment(
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        location: str | None = None,
    ):
        """Create a new appointment in the calendar using the specified parameters."""
        event = {
            "summary": summary,
            "location": location,
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC",
            },
        }
        return service.events().insert(calendarId=gc_config.calendar_id, body=event).execute()

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def get_next_appointment():
        """Get the next appointment in the calendar."""
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(calendarId=gc_config.calendar_id, timeMin=now, maxResults=1, singleEvents=True, orderBy="startTime")
            .execute()
        )
        events = events_result.get("items", [])
        return events[0] if len(events) > 0 else None

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def delete_appointment_by_time(start_time: str):
        """Delete the appointment with the specified start time."""
        events_result = (
            service.events()
            .list(
                calendarId=gc_config.calendar_id,
                timeMin=start_time,
                maxResults=1,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if events:
            event_id = events[0]["id"]
            service.events().delete(calendarId=gc_config.calendar_id, eventId=event_id).execute()
            return True
        return False

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def delete_appointment_by_id(appointment_id: int) -> bool:
        service.events().delete(calendarId=gc_config.calendar_id, eventId=appointment_id).execute()
        return True

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def delete_next_appointment() -> bool:
        """Delete the next appointment in the calendar."""
        event = CalendarAPI.get_next_appointment()
        return event and CalendarAPI.delete_appointment_by_id(appointment_id=event["id"])

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def delete_all_appointments_today():
        """Delete all the today's appointments in the calendar."""
        start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time.min).isoformat() + "Z"
        end_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time.max).isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId=gc_config.calendar_id,
                timeMin=start_of_day,
                timeMax=end_of_day,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        for event in events:
            service.events().delete(calendarId=gc_config.calendar_id, eventId=event["id"]).execute()
        return True

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def list_appointments(time_start: str, time_end: str) -> list:
        """list all the appointments in the calendar."""
        events_result = (
            service.events()
            .list(
                calendarId=gc_config.calendar_id,
                timeMin=time_start,
                timeMax=time_end,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def am_i_free(time: str | None = None) -> bool:
        """Determine if I have no appointments among the specified time."""
        return (
            len(
                CalendarAPI.list_appointments(
                    time_start=time,
                    time_end=time,
                ),
            )
            == 0
        )

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def am_i_free_in_the_next(hours: int = 2) -> bool:
        """Determine if I have no appointments in the next specified (defaults to 2) hours."""
        return (
            len(
                CalendarAPI.list_appointments(
                    time_start=format_datetime(dt=datetime.datetime.now(datetime.UTC)),
                    time_end=format_datetime(dt=datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=hours)),
                ),
            )
            == 0
        )

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def list_todays_appointments():
        """list all the today's appointments in the calendar."""
        return CalendarAPI.list_appointments(
            time_start=format_datetime(dt=datetime.datetime.combine(datetime.date.today(), datetime.time.min)),
            time_end=format_datetime(dt=datetime.datetime.combine(datetime.date.today(), datetime.time.max)),
        )

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def list_this_weeks_appointments():
        """list all the today's appointments in the calendar."""
        today = datetime.date.today()
        start_of_week = (today - datetime.timedelta(days=today.weekday())).isoformat() + "T00:00:00Z"
        end_of_week = (today + datetime.timedelta(days=6 - today.weekday())).isoformat() + "T23:59:59Z"
        return CalendarAPI.list_appointments(
            time_start=start_of_week,
            time_end=end_of_week,
        )

    @staticmethod
    @catch_http_exception
    @intent.mark_intent
    def list_calendars() -> list:
        """list all the calendars in the account."""
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        for calendar in calendars:
            logger.info(f"ID: {calendar['id']}, Summary: {calendar['summary']}")
        return calendars


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO 8601 format with UTC timezone"""
    return dt.replace(tzinfo=datetime.UTC).isoformat()


if __name__ == "__main__":
    intent_manager = IntentManager()
    for name, docstring in intent.get_marked_functions_and_docstrings(module=CalendarAPI).items():
        intent_manager.add_intent(
            intent.Intent(
                name=name,
                description=docstring,
            ),
        )
    print(intent_manager)

    test_calendar = False
    if test_calendar:
        new_event = CalendarAPI.create_new_appointment(
            summary="Team Meeting",
            start_time=format_datetime(datetime.datetime.now(datetime.UTC)),
            end_time=format_datetime(datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)),
            description="Discuss project updates",
            location="Conference Room",
        )
        print("New Event Created:", new_event)

        next_appointment = CalendarAPI.get_next_appointment()
        print("Next Appointment:", json.dumps(next_appointment, indent=2))

        print(f"Am I free In the next 2 hours: {CalendarAPI.am_i_free_in_the_next()}")
        print(f"Am I free Now: {CalendarAPI.am_i_free(time=format_datetime(datetime.datetime.now(datetime.UTC)))}")
        print(f"Deleted next appointment: {CalendarAPI.delete_next_appointment()}")
