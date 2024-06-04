from src.web_handler.calendar_api import CalendarAPI

GET_NEXT_APPOINTMENT = """
[INST]
You are a help desk client.
You can convert structured data into proper responses in natural language

Example1:
user: What's my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Meeting with Mom",
  "description": "To discuss party plans",
  "location": "Her House",
  "creator": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "organizer": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "start": {{
    "dateTime": "2024-06-04T17:00:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "end": {{
    "dateTime": "2024-06-04T18:15:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "iCalUID": "3t7qd0dd4mpe86prhpbcdrg8ec@google.com",
  "sequence": 0,
  "reminders": {{
    "useDefault": true
  }},
  "eventType": "default"
  "now": "2024-06-04T14:00:00+02:00"
}}
answer: You should meet your mom at her house at 17 o'clock (roughly in 3 hours). You're going to plan a party with her. 

Example1:
user: What's my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Meeting with Mom",
  "description": "To discuss party plans",
  "location": "Her House",
  "creator": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "organizer": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "start": {{
    "dateTime": "2024-06-04T17:00:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "end": {{
    "dateTime": "2024-06-04T18:15:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "iCalUID": "3t7qd0dd4mpe86prhpbcdrg8ec@google.com",
  "sequence": 0,
  "reminders": {{
    "useDefault": true
  }},
  "eventType": "default"
  "now": "2024-06-04T14:00:00+02:00"
}}
answer: You should meet your mom at her house at 17 o'clock (roughly in 3 hours). You're going to plan a party with her. 

Example2:
user: What's my next appointment?
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
[/INST]
answer:
"""

DELETE_NEXT_APPOINTMENT = """
[INST]
You are a help desk client.
You can convert structured data into proper responses in natural language

Example1:
user: Can you delete my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Meeting with Mom",
  "description": "To discuss party plans",
  "location": "Her House",
  "creator": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "organizer": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "start": {{
    "dateTime": "2024-06-04T17:00:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "end": {{
    "dateTime": "2024-06-04T18:15:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "iCalUID": "3t7qd0dd4mpe86prhpbcdrg8ec@google.com",
  "sequence": 0,
  "reminders": {{
    "useDefault": true
  }},
  "eventType": "default"
  "now": "2024-06-04T14:00:00+02:00"
}}
answer: Sure, your next appointment with your mom, which was supposed to happen today at 17 o'clock has been canceled. Make sure your mom also knows about that.

Example1:
user: What's my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Meeting with Mom",
  "description": "To discuss party plans",
  "location": "Her House",
  "creator": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "organizer": {{
    "email": "butlerkit2024@gmail.com",
    "self": true
  }},
  "start": {{
    "dateTime": "2024-06-04T17:00:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "end": {{
    "dateTime": "2024-06-04T18:15:00+02:00",
    "timeZone": "Europe/Berlin"
  }},
  "iCalUID": "3t7qd0dd4mpe86prhpbcdrg8ec@google.com",
  "sequence": 0,
  "reminders": {{
    "useDefault": true
  }},
  "eventType": "default"
  "now": "2024-06-04T14:00:00+02:00"
}}
answer: You should meet your mom at her house at 17 o'clock (roughly in 3 hours). You're going to plan a party with her. 

Example2:
user: What's my next appointment?
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
[/INST]
answer:
"""

calendar_api_respond_prompts: dict[str, str] = {
    CalendarAPI.get_next_appointment.__name__: GET_NEXT_APPOINTMENT,
    CalendarAPI.delete_next_appointment.__name__: DELETE_NEXT_APPOINTMENT,
}


def get_calendar_api_respond_prompts(function: str) -> str:
    if function not in calendar_api_respond_prompts:
        err_msg = f"Respond Prompt for '{function}' is not registered yet."
        raise ValueError(err_msg)
    return calendar_api_respond_prompts[function]
