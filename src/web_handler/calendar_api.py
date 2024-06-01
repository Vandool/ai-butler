import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src import utils
from src.config import google_api_config

# Authentication and service creation
SCOPES = ["https://www.googleapis.com/auth/calendar"]

gc_config = google_api_config.get_google_api_config()

credentials = service_account.Credentials.from_service_account_info(
    google_api_config.get_service_account_info(config=gc_config),
    scopes=SCOPES,
)
service = build("calendar", "v3", credentials=credentials)
logger = utils.get_logger("CalendarAPI")


class CalendarAPI:
    @staticmethod
    def get_next_appointment():
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(calendarId=gc_config.calendar_id, timeMin=now, maxResults=1, singleEvents=True, orderBy="startTime")
            .execute()
        )
        events = events_result.get("items", [])
        return events[0] if len(events) > 0 else None

    @staticmethod
    def create_new_appointment(summary, start_time, end_time, description=None, location=None):
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
    def delete_appointment_by_time(start_time):
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
    def delete_next_appointment():
        event = CalendarAPI.get_next_appointment()
        if event:
            service.events().delete(calendarId=gc_config.calendar_id, eventId=event["id"]).execute()
            return True
        return False

    @staticmethod
    def delete_appointment_by_id(appointment_id):
        service.events().delete(calendarId=gc_config.calendar_id, eventId=appointment_id).execute()
        return True

    @staticmethod
    def delete_all_appointments_today():
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
    def am_i_free(time: str) -> bool:
        events_result = (
            service.events()
            .list(calendarId=gc_config.calendar_id, timeMin=time, timeMax=time, singleEvents=True, orderBy="startTime")
            .execute()
        )
        events = events_result.get("items", [])
        return len(events) == 0

    @staticmethod
    def list_todays_appointments():
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
        return events_result.get("items", [])

    @staticmethod
    def list_this_weeks_appointments():
        today = datetime.date.today()
        start_of_week = (today - datetime.timedelta(days=today.weekday())).isoformat() + "T00:00:00Z"
        end_of_week = (today + datetime.timedelta(days=6 - today.weekday())).isoformat() + "T23:59:59Z"
        events_result = (
            service.events()
            .list(
                calendarId=gc_config.calendar_id,
                timeMin=start_of_week,
                timeMax=end_of_week,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    @staticmethod
    def list_appointments(time_start, time_end):
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
    def list_calendars() -> list:
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])
        for calendar in calendars:
            logger.info(f"ID: {calendar['id']}, Summary: {calendar['summary']}")
        return calendars


# Function to format datetime to ISO 8601 format with UTC timezone
def format_datetime(dt):
    return dt.replace(tzinfo=datetime.UTC).isoformat()


if __name__ == "__main__":
    # next_appointment = CalendarAPI.get_next_appointment()
    # print("Next Appointment:", json.dumps(next_appointment, indent=2))
    #
    # CalendarAPI.list_calendars()
    #
    new_event = CalendarAPI.create_new_appointment(
        summary="Team Meeting",
        start_time=format_datetime(datetime.datetime.now(datetime.UTC)),
        end_time=format_datetime(datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)),
        description="Discuss project updates",
        location="Conference Room",
    )

    print("New Event Created:", new_event)
