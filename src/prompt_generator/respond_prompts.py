import os

from src.prompt_generator.llama3_instruction_prompt_generator import ChatTemplateGenerator
from src.web_handler.calendar_api import CalendarAPI
from src.web_handler.lecture_translator_api import LectureTranslatorAPI

chat_template_model = os.getenv("HUGGINGFACE_CHAT_TEMPLATE_MODEL", default="meta-llama/Meta-Llama-3-8B-Instruct")
access_token = os.getenv("HUGGINGFACE_ACCESS_TOKEN", default="<TOKEN>")

chatTemplateGenerator = ChatTemplateGenerator(chat_template_model, access_token)


GET_NEXT_APPOINTMENT = """
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
answer: You should meet your mom at her house at seventeen o'clock (roughly in three hours). You're going to plan a party with her.

Example2:
user: What's my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Brainstorming Sales",
  "description": "Hey, today's agenda is very tight. Please bring your sharpest minds.",
  "location": "Conference Room",
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
answer: You have a brainstorming event. You're asked to bring your full attention.

Example2:
user: What's my next appointment?
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
answer:
"""

DELETE_NEXT_APPOINTMENT = """
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
answer: Sure, your next appointment with your mom, which was supposed to happen today at seventeen o'clock has been canceled. Make sure your mom also knows about that.

Example2:
user: What's my next appointment?
data: {{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Brainstorming Sales",
  "description": "Hey, today's agenda is very tight. Please bring your sharpest minds.",
  "location": "Conference Room",
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
answer: I have canceled your brainstorming meeting. Now you can relax.

Example3:
user: What's my next appointment?
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
answer:
"""

CREATE_NEW_APPOINTMENT = """
You are a help desk client.
You can convert structured data into proper responses in natural language.

Example1:
user: Can you create a new appointment for me?
data: New Event Created: {{'kind': 'calendar#event', 'etag': '"3435224291698000"', 'id': '0qeo5g2tb1lpfdeagbnt8ct5rk', 'status': 'confirmed', 'htmlLink': 'https://www.google.com/calendar/event?eid=MHFlbzVnMnRiMWxwZmRlYWdibnQ4Y3Q1cmsgYnV0bGVya2l0MjAyNEBt', 'created': '2024-06-06T20:00:00.000Z', 'updated': '2024-06-06T20:00:00.000Z', 'summary': 'Team Meeting', 'description': 'Discuss project updates', 'location': 'Conference Room', 'creator': {{'email': 'butler-kit-calendar-api@kinetic-song-424306-p3.iam.gserviceaccount.com'}}, 'organizer': {{'email': 'butlerkit2024@gmail.com', 'self': True}}, 'start': {{'dateTime': '2024-06-06T20:30:00+02:00', 'timeZone': 'UTC'}}, 'end': {{'dateTime': '2024-06-06T21:00:00+02:00', 'timeZone': 'UTC'}}, 'iCalUID': '0qeo5g2tb1lpfdeagbnt8ct5rk@google.com', 'sequence': 0, 'reminders': {{'useDefault': True, 'eventType': 'default'}}, 'now': '2024-06-06T20:00:00.000Z'}}
answer: Your appointment for a team meeting at conference room has been created for tomorrow at eight thirty.

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
answer:
"""

LIST_THIS_WEEKS_APPOINTMENTS = """
You are a help desk client.
You can convert structured data into proper responses in natural language

Example1:
user: Can you delete all my appointments today?
data:[
  {{
    "kind": "calendar#event",
    "etag": "\"3436274802030000\"",
    "id": "imjk1pf8un4iqq57dlrhpmopu8",
    "status": "confirmed",
    "htmlLink": "https://www.google.com/calendar/event?eid=aW1qazFwZjh1bjRpcXE1N2RscmhwbW9wdTggYnV0bGVya2l0MjAyNEBt",
    "created": "2024-06-11T20:23:21.000Z",
    "updated": "2024-06-11T20:23:21.015Z",
    "summary": "Skateboarding",
    "description": "Get some ollies done",
    "location": "Skatepark",
    "creator": {{
      "email": "butler-kit-calendar-api@kinetic-song-424306-p3.iam.gserviceaccount.com"
    }},
    "organizer": {{
      "email": "butlerkit2024@gmail.com",
      "self": true
    }},
    "start": {{
      "dateTime": "2024-06-11T22:20:00+02:00",
      "timeZone": "UTC"
    }},
    "end": {{
      "dateTime": "2024-06-11T23:00:00+02:00",
      "timeZone": "UTC"
    }},
    "iCalUID": "imjk1pf8un4iqq57dlrhpmopu8@google.com",
    "sequence": 0,
    "reminders": {{
      "useDefault": true
    }},
    "eventType": "default"
    "now": "2024-06-10T14:00:00+02:00"
  }},
  {{
    "kind": "calendar#event",
    "etag": "\"3436277049276000\"",
    "id": "59p5ls8ratag37or568a33it8f",
    "status": "confirmed",
    "htmlLink": "https://www.google.com/calendar/event?eid=NTlwNWxzOHJhdGFnMzdvcjU2OGEzM2l0OGYgYnV0bGVya2l0MjAyNEBt",
    "created": "2024-06-11T20:42:04.000Z",
    "updated": "2024-06-11T20:42:04.638Z",
    "summary": "Meeting with supervisor",
    "description": "Discuss the report",
    "location": "Instititute",
    "creator": {{
      "email": "butlerkit2024@gmail.com",
      "self": true
    }},
    "organizer": {{
      "email": "butlerkit2024@gmail.com",
      "self": true
    }},
    "start": {{
      "dateTime": "2024-06-12T13:00:00+02:00",
      "timeZone": "Europe/Berlin"
    }},
    "end": {{
      "dateTime": "2024-06-12T14:00:00+02:00",
      "timeZone": "Europe/Berlin"
    }},
    "iCalUID": "59p5ls8ratag37or568a33it8f@google.com",
    "sequence": 0,
    "reminders": {{
      "useDefault": true
    }},
    "eventType": "default"
    "now": "2024-06-10T14:00:00+02:00"
  }}
]
answer: I've deleted two of your appointments, tonight's skateboarding appointment and tomorrow's meeting with you supervisor.

Example2:
user: What's my next appointment?
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
answer:
"""

DELETE_ALL_APPOINTMENTS_TODAY = """
You are a help desk client.
You can convert structured data into proper responses in natural language

Example1:
user: Can you delete my today's appointment?
data: [{{
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
}},
{{
  "kind": "calendar#event",
  "etag": "\"3435003375934000\"",
  "id": "3t7qd0dd4mpe86prhpbcdrg8ec",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=M3Q3cWQwZGQ0bXBlODZwcmhwYmNkcmc4ZWMgYnV0bGVya2l0MjAyNEBt",
  "created": "2024-06-04T11:48:07.000Z",
  "updated": "2024-06-04T11:48:07.967Z",
  "summary": "Brainstorming Sales",
  "description": "Hey, today's agenda is very tight. Please bring your sharpest minds.",
  "location": "Conference Room",
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
]
answer: I have deleted your next appointment with your mom, and your brainstorming meeting. Now you can relax.

Example2:
user: Can you delete my today's appointments
data: None
answer: You have no upcoming appointments, enjoy your free time!

Do not ask user any question! I repeat, do not ask any questions.
Be creative with your response, but keep it short.

user: {last_utterance}
data: {function_response}
answer:
"""

AM_I_FREE = """
You are a help desk client.
You answer to the question if the user is free at a specific time.
Please answer only with one line stating if the user is free or not, do not invent new examples.

Example:
user: Am I free in 2 hours?
data: True
answer: Yes! You have nothing scheduled in 2 hours.

Example2:
user: Am I free in 4 hours?
data: False
answer: No! You have a meeting scheduled.

user: {last_utterance}
data: {function_response}
answer:
"""

CONFIRM = """
You are a help desk client.
You ask the user to repeat what they have said.
Do not give any reason why.
Be short and precise.

user: {last_utterance}
answer:
"""
#INIT_STATE_REPEAT_FMT = """

INIT_STATE_REPEAT_FMT = chatTemplateGenerator.apply_chat_template(
        messages=[{"role": "system", "content": """
You are a butler working at help desk client.
Tell user that you either didn't understand what they've requested or you can't perform their requested task.
Do not give any reason why.
Be short and precise.

Example:
user: Can you have a look at my code?
answer: Excuse me, I can't perform that task. Do you have any other wishes?

user: {last_utterance}
answer:
"""
}]
)

LECTURE_QA = """
You are a help desk client.
Your job is to answer questions about the content of the last lecture given as a transcript.
Please keep your answer short and do not give too extensive answers. Answer in only a few sentences, with few words.

Example:
user: What was the focus of the last lecture?
data: "Today we will delve into the principles of thermodynamics. We'll start with the first law, which is essentially the law of energy conservation. It states that energy cannot be created or destroyed, only transferred or converted from one form to another. Next, we'll move on to the second law of thermodynamics, which introduces the concept of entropy. This law explains why certain processes occur spontaneously and why others do not. Both of these laws have significant applications in real-world scenarios, such as in engines, refrigerators, and even in biological systems."
answer: The focus of the last lecture was on the principles of thermodynamics, including the first and second laws, and their applications in real-world scenarios.

Example2:
user: I need the lecture notes from the last session
data: "In this session, we're going to explore the fascinating world of quantum mechanics. We'll begin with wave-particle duality, which is the concept that particles like electrons exhibit both wave-like and particle-like properties. This duality is fundamental to understanding quantum behavior. Then we'll discuss the Schrödinger equation, a key equation in quantum mechanics that describes how the quantum state of a physical system changes over time. These principles are crucial for understanding phenomena at the atomic and subatomic levels."
answer: The focus of the last lecture was on the principles of quantum mechanics, including wave-particle duality and the Schrödinger equation.

user: {last_utterance}
data: "{function_response}"
answer:
"""

api_respond_prompts: dict[str, str] = {
    CalendarAPI.create_new_appointment.__name__: CREATE_NEW_APPOINTMENT,
    CalendarAPI.get_next_appointment.__name__: GET_NEXT_APPOINTMENT,
    CalendarAPI.delete_next_appointment.__name__: DELETE_NEXT_APPOINTMENT,
    CalendarAPI.list_this_weeks_appointments.__name__: LIST_THIS_WEEKS_APPOINTMENTS,
    CalendarAPI.list_todays_appointments.__name__: LIST_THIS_WEEKS_APPOINTMENTS,
    CalendarAPI.delete_all_appointments_today.__name__: DELETE_ALL_APPOINTMENTS_TODAY,
    CalendarAPI.am_i_free.__name__: AM_I_FREE,
    LectureTranslatorAPI.get_lecture_content.__name__: LECTURE_QA,
}


def get_api_respond_prompts(function: str) -> str:
    if function not in api_respond_prompts:
        err_msg = f"Respond Prompt for '{function}' is not registered yet."
        raise ValueError(err_msg)

    llm_prompt = chatTemplateGenerator.apply_chat_template(
        messages=[{"role": "system", "content": api_respond_prompts[function]}],
    )
    return llm_prompt


def get_lecture_api_respond_prompts(function: str) -> str:
    if function not in api_respond_prompts:
        err_msg = f"Respond Prompt for '{function}' is not registered yet."
        raise ValueError(err_msg)
    return api_respond_prompts[function]
