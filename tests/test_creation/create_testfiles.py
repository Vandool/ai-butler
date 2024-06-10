import shutil

from gradio_client import Client

client = Client("mrfakename/MeloTTS")

class CALENDAR:
    name = ""

get_next_appointment = [
    # path_to_audio_file, text, intent
    # Google Calendar get_next_appointment
    ("get_next_appointment1.mp3", "Hey butler, what's my upcoming event?", CALENDAR.name),
    ("get_next_appointment2.mp3", "Okay butler, what's next in my calendar?", CALENDAR.name),
    ("get_next_appointment3.mp3", "Hey butler, so what are we doing next?", CALENDAR.name),
    ("get_next_appointment4.mp3", "Okay butler, can you get my next appointment?", CALENDAR.name),
    ("get_next_appointment5.mp3", "Hey butler, what is my next appointment?", CALENDAR.name),
    ("get_next_appointment6.mp3", "Okay butler, please tell me my next meeting", CALENDAR.name),
    ("get_next_appointment7.mp3", "Hey butler, tell me what my next meeting is", CALENDAR.name),
    ("get_next_appointment8.mp3", "Okay butler, what's up next in my calendar?", CALENDAR.name),
    ("get_next_appointment9.mp3", "Hey butler, tell me my next meeting", CALENDAR.name),
    ("get_next_appointment10.mp3", "Okay butler, please tell me my next scheduled appointment.", CALENDAR.name),
]

list_this_weeks_appointments = [
    # Google Calendar list_this_weeks_appointments
    ("list_this_weeks_appointments1.mp3", "Hey butler, what commitments do I have this week?", CALENDAR.name),
    ("list_this_weeks_appointments2.mp3", "Okay butler, show me all my appointments for this week.", CALENDAR.name),
    ("list_this_weeks_appointments3.mp3", "Hey butler, what appointments do I have lined up this week?", CALENDAR.name),
    ("list_this_weeks_appointments4.mp3", "Okay butler, list my schedule for the current week.", CALENDAR.name),
    ("list_this_weeks_appointments5.mp3", "Hey butler, can you tell me my meetings for this week?", CALENDAR.name),
    ("list_this_weeks_appointments6.mp3", "Okay butler, I need to know all the appointments I have this week.",
     CALENDAR.name),
    ("list_this_weeks_appointments7.mp3", "Hey butler, what are my plans for this week?", CALENDAR.name),
    ("list_this_weeks_appointments8.mp3", "Okay butler, please list my engagements for this week.", CALENDAR.name),
    ("list_this_weeks_appointments9.mp3", "Hey butler, tell me my schedule for this week.", CALENDAR.name),
    ("list_this_weeks_appointments10.mp3", "Okay butler, what do I have scheduled this week?", CALENDAR.name),
]

delete_next_appointment = [
    # Google Calendar delete_next_appointment
    ("delete_next_appointment1.mp3", "Hey butler, I want to cancel my next appointment.", CALENDAR.name),
    ("delete_next_appointment2.mp3", "Okay butler, can you please cancel the next meeting?", CALENDAR.name),
    ("delete_next_appointment3.mp3",
     "Hey butler, oh, I am already tired from all these meetings, can you please remove the next one?", CALENDAR.name),
    ("delete_next_appointment4.mp3", "Okay butler, please delete my next appointment.", CALENDAR.name),
    ("delete_next_appointment5.mp3", "Hey butler, cancel my next meeting.", CALENDAR.name),
    ("delete_next_appointment6.mp3", "Okay butler, can you remove my upcoming appointment?", CALENDAR.name),
    ("delete_next_appointment7.mp3", "Hey butler, I need you to cancel my next appointment.", CALENDAR.name),
    ("delete_next_appointment8.mp3", "Okay butler, could you please delete my next meeting?", CALENDAR.name),
    ("delete_next_appointment9.mp3", "Hey butler, please cancel my next scheduled event.", CALENDAR.name),
    ("delete_next_appointment10.mp3", "Okay butler, can you delete my next calendar entry?", CALENDAR.name),
]

list_todays_appointments = [
    # Google Calendar list_todays_appointments
    ("list_todays_appointments1.mp3", "Hey butler, please list today's events.", CALENDAR.name),
    ("list_todays_appointments2.mp3", "Okay butler, show me today's schedule.", CALENDAR.name),
    ("list_todays_appointments3.mp3", "Hey butler, what events are on my calendar for today?", CALENDAR.name),
    ("list_todays_appointments4.mp3", "Okay butler, can you list my appointments for today?", CALENDAR.name),
    ("list_todays_appointments5.mp3", "Hey butler, tell me my meetings for today.", CALENDAR.name),
    ("list_todays_appointments6.mp3", "Okay butler, what do I have scheduled for today?", CALENDAR.name),
    ("list_todays_appointments7.mp3", "Hey butler, please show me my calendar for today.", CALENDAR.name),
    ("list_todays_appointments8.mp3", "Okay butler, what is on my agenda today?", CALENDAR.name),
    ("list_todays_appointments9.mp3", "Hey butler, I need to know my appointments for today.", CALENDAR.name),
    ("list_todays_appointments10.mp3", "Okay butler, what are my plans for today?", CALENDAR.name),
]

delete_all_appointments_today = [
    # Google Calendar delete_all_appointments_today
    ("delete_all_appointments_today1.mp3", "Hey butler, erase all today's appointments.", CALENDAR.name),
    ("delete_all_appointments_today2.mp3", "Okay butler, can you remove all of today's meetings?", CALENDAR.name),
    ("delete_all_appointments_today3.mp3", "Hey butler, please cancel all my appointments today.", CALENDAR.name),
    ("delete_all_appointments_today4.mp3", "Okay butler, I need to delete all of today's events.", CALENDAR.name),
    ("delete_all_appointments_today5.mp3", "Hey butler, clear my calendar for today.", CALENDAR.name),
    ("delete_all_appointments_today6.mp3", "Okay butler, cancel everything on my schedule for today.", CALENDAR.name),
    ("delete_all_appointments_today7.mp3", "Hey butler, can you delete all today's appointments?", CALENDAR.name),
    ("delete_all_appointments_today8.mp3", "Okay butler, remove all events for today.", CALENDAR.name),
    ("delete_all_appointments_today9.mp3", "Hey butler, please delete all today's meetings.", CALENDAR.name),
    ("delete_all_appointments_today10.mp3", "Okay butler, I want to cancel all my appointments for today.",
     CALENDAR.name),
]

for i, test in enumerate(delete_all_appointments_today):
    result = client.predict(
        text=test[1],
        speaker="EN-Default",
        speed=1,
        language="EN",
        api_name="/synthesize"
    )

    shutil.copy(result, "../test_data/" + test[0].split(".mp3")[0][:-1] + str(i+1) + ".mp3")
    print(test[1])