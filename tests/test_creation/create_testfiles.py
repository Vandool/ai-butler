import shutil

from gradio_client import Client

client = Client("mrfakename/MeloTTS")

class CALENDAR:
    name = ""

class LECTURE:
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

am_i_free = [
    ("am_i_free0.mp3", "Hey butler, am I free tomorrow at 3 PM?", CALENDAR.name),
    ("am_i_free1.mp3", "Okay butler, do I have any appointments in 5 hours?", CALENDAR.name),
    ("am_i_free2.mp3", "Hey butler, am I free next Monday at 10 AM?", CALENDAR.name),
    ("am_i_free3.mp3", "Okay butler, do I have anything scheduled for next week at 2 PM?", CALENDAR.name),
    ("am_i_free4.mp3", "Hey butler, am I free this Friday at noon?", CALENDAR.name),
    ("am_i_free5.mp3", "Okay butler, do I have any meetings in 3 days at 4 PM?", CALENDAR.name),
    ("am_i_free6.mp3", "Hey butler, am I available in 7 hours?", CALENDAR.name),
    ("am_i_free7.mp3", "Okay butler, do I have anything booked next Tuesday at 9 AM?", CALENDAR.name),
    ("am_i_free8.mp3", "Hey butler, am I free next weekend at 1 PM?", CALENDAR.name),
    ("am_i_free9.mp3", "Okay butler, do I have any plans in two weeks at 11 AM?", CALENDAR.name),
]

get_lecture_content = [
    ("get_lecture_content0.mp3", "Hey butler, can you get the content of the last lecture?", LECTURE.name),
    ("get_lecture_content1.mp3", "Okay butler, what was discussed in the recent lecture?", LECTURE.name),
    ("get_lecture_content2.mp3", "Hey butler, please give me the transcript of the previous lecture.", LECTURE.name),
    ("get_lecture_content3.mp3", "Okay butler, could you fetch the content of yesterday's lecture?", LECTURE.name),
    ("get_lecture_content4.mp3", "Hey butler, can you show me the details of the last lecture?", LECTURE.name),
    ("get_lecture_content5.mp3", "Okay butler, what topics were covered in the last lecture?", LECTURE.name),
    ("get_lecture_content6.mp3", "Hey butler, give me the notes from the recent lecture.", LECTURE.name),
    ("get_lecture_content7.mp3", "Okay butler, please provide the content of the last lecture session.", LECTURE.name),
    ("get_lecture_content8.mp3", "Hey butler, what did the professor talk about in the last lecture?", LECTURE.name),
    ("get_lecture_content9.mp3", "Okay butler, what was the lecture about last time?", LECTURE.name),
]

create_appointment = [
    [("create_appointment0_0.mp3",
      "Hey butler, please create an appointment tomorrow from 10 to 11 titled 'Team Meeting' in the Conference Room.")],
    [("create_appointment1_0.mp3",
      "Hey butler, schedule an appointment next Monday from 2 PM to 3 PM titled 'Project Review'.")],
    [("create_appointment2_0.mp3",
      "Hey butler, set up a meeting next Friday from 9 AM to 10 AM titled 'Weekly Sync' with description 'Weekly team sync-up'.")],

    # Dialogs where the end time is provided after the initial request
    [("create_appointment3_0.mp3", "Hey butler, create an appointment tomorrow at 10 titled 'Client Call'."),
     ("create_appointment3_1.mp3", "It ends at 11.")],
    [("create_appointment4_0.mp3",
      "Hey butler, schedule an appointment next Monday at 2 PM titled 'Doctor's Appointment'."),
     ("create_appointment4_1.mp3", "It should end at 3 PM.")],

    # Dialogs where the system asks for the end time after some optional parameters are provided
    [("create_appointment5_0.mp3", "Hey butler, create an appointment tomorrow at 10."),
     ("create_appointment5_1.mp3", "Title it 'Team Sync'."),
     ("create_appointment5_2.mp3", "It should end at 11.")],

    [("create_appointment6_0.mp3", "Hey butler, schedule a meeting next Tuesday at 1 PM."),
     ("create_appointment6_1.mp3", "Description is 'Project Discussion'."),
     ("create_appointment6_2.mp3", "It ends at 2 PM.")],

    # Dialogs with additional optional parameters provided in the initial request
    [("create_appointment7_0.mp3",
      "Hey butler, create an appointment tomorrow from 10 to 11 titled 'Team Meeting' with description 'Discuss project updates'.")],
    [("create_appointment8_0.mp3",
      "Hey butler, schedule an appointment next Monday from 2 PM to 3 PM with title 'Project Discussion' at 'Conference Room'.")],
    [("create_appointment9_0.mp3",
      "Hey butler, set up a meeting next Friday from 9 AM to 10 AM titled 'Strategy Session' with location 'Meeting Room 1'.")]
]

for i, dialog in enumerate(create_appointment):
    for i, test in enumerate(dialog):
        result = client.predict(
            text=test[1],
            speaker="EN-Default",
            speed=1,
            language="EN",
            api_name="/synthesize"
        )

        shutil.copy(result, "../test_data_temp/" + test[0].split(".mp3")[0][:-1] + str(i+1) + ".mp3")
        print(test[1])