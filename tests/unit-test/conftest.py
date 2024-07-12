# tests/unit-test/conftest.py
import datetime
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from src.classifier.base_classifier import BaseClassifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
#from src.classifier.ollama_classifier import OllamaClassifier
from src.config.asr_llm_config import AsrLlmConfig
from src.intent.intent import CALENDAR, LECTURE
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient

# ----------------------------- Reusable Fixtures -----------------------------

load_dotenv()

one_off_test = ("get_next_appointment13.mp3", "Hey butler, whats up next?", CALENDAR.name),

dialog_test_data = [
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
      "Hey butler, set up a meeting next Friday from 9 AM to 10 AM titled 'Strategy Session' with location 'Meeting Room 1'.")],

    # Dialogs with only the start time initially, followed by optional parameters, then the end time
    [("create_appointment10_0.mp3", "Hey butler, create an appointment tomorrow at 10."),
     ("create_appointment10_1.mp3", "Title it 'Team Meeting'."),
     ("create_appointment10_2.mp3", "It should end at 11.")],

    [("create_appointment11_0.mp3", "Hey butler, schedule an appointment next Monday at 2 PM."),
     ("create_appointment11_1.mp3", "Location is 'Conference Room'."),
     ("create_appointment11_2.mp3", "It ends at 3 PM.")],

    # Dialogs with title given first, then start time, followed by optional parameters and end time
    [("create_appointment12_0.mp3", "Hey butler, create an appointment titled 'Team Sync'."),
     ("create_appointment12_1.mp3", "It starts tomorrow at 10."),
     ("create_appointment12_2.mp3", "Description is 'Weekly team sync-up'."),
     ("create_appointment12_3.mp3", "It should end at 11.")],

    [("create_appointment13_0.mp3", "Hey butler, schedule a meeting titled 'Client Presentation'."),
     ("create_appointment13_1.mp3", "It starts next Monday at 2 PM."),
     ("create_appointment13_2.mp3", "Location is 'Main Hall'."),
     ("create_appointment13_3.mp3", "It should end at 3 PM.")],

    # Longer dialogs with multiple interactions for all parameters
    [("create_appointment14_0.mp3", "Hey butler, create an appointment titled 'Team Sync'."),
     ("create_appointment14_1.mp3", "It starts tomorrow at 10."),
     ("create_appointment14_2.mp3", "Description is 'Weekly team sync-up'."),
     ("create_appointment14_3.mp3", "Location is 'Office Room 1'."),
     ("create_appointment14_4.mp3", "It ends at 11.")],

    [("create_appointment15_0.mp3", "Hey butler, schedule an appointment titled 'Client Meeting'."),
     ("create_appointment15_1.mp3", "It starts next Monday at 2 PM."),
     ("create_appointment15_2.mp3", "Description is 'Discuss quarterly report'."),
     ("create_appointment15_3.mp3", "Location is 'Meeting Room 2'."),
     ("create_appointment15_4.mp3", "It ends at 3 PM.")],

    [("create_appointment16_0.mp3", "Hey butler, set up a meeting titled 'Project Kickoff'."),
     ("create_appointment16_1.mp3", "It starts next Friday at 9 AM."),
     ("create_appointment16_2.mp3", "Description is 'Kickoff for the new project'."),
     ("create_appointment16_3.mp3", "Location is 'Conference Hall'."),
     ("create_appointment16_4.mp3", "It should end at 10 AM.")],

    [("create_appointment17_0.mp3", "Hey butler, please create an appointment on Wednesday from 3 PM to 4 PM titled 'Budget Meeting' in Room 5.")],

    [("create_appointment18_0.mp3", "Hey butler, create an appointment on Thursday at 11 AM."),
     ("create_appointment18_1.mp3", "Title it 'HR Meeting'."),
     ("create_appointment18_2.mp3", "Description is 'Discuss new hires'."),
     ("create_appointment18_3.mp3", "It should end at 12 PM.")],

    # Dialogs where title is given first, then start time, followed by end time and other optional parameters
    [("create_appointment19_0.mp3", "Hey butler, create an appointment titled 'One-on-One Meeting'."),
     ("create_appointment19_1.mp3", "It starts next Thursday at 2 PM."),
     ("create_appointment19_3.mp3", "Description is 'Weekly one-on-one with manager'."),
     ("create_appointment19_4.mp3", "Location is 'Manager's Office'."),
     ("create_appointment19_2.mp3", "It should end at 3 PM.")],

    # Dialogs where the end time is provided after the initial request
    [("create_appointment20_0.mp3", "Hey butler, schedule an appointment next Friday at 10 AM."),
     ("create_appointment20_1.mp3", "Title it 'Team Check-In'."),
     ("create_appointment20_2.mp3", "Location is 'Conference Room A'."),
     ("create_appointment20_3.mp3", "It ends at 11 AM.")]
]

one_off_test_data = [
    # path_to_audio_file, text, intent
    # Google Calendar get_next_appointment
    ("get_next_appointment0.mp3", "Hey butler, when is my next scheduled event?", CALENDAR.name),
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
    ("get_next_appointment11.mp3", "Hey butler, what's on my calendar next?", CALENDAR.name),
    ("get_next_appointment12.mp3", "Okay butler, what's my next event?", CALENDAR.name),
    ("get_next_appointment13.mp3", "Hey butler, can you tell me my next event?", CALENDAR.name),
    ("get_next_appointment14.mp3", "Okay butler, what's the next thing on my schedule?", CALENDAR.name),
    ("get_next_appointment15.mp3", "Hey butler, what's coming up next in my calendar?", CALENDAR.name),
    ("get_next_appointment16.mp3", "Okay butler, when is my next event?", CALENDAR.name),
    ("get_next_appointment17.mp3", "Hey butler, what is my next scheduled event?", CALENDAR.name),
    ("get_next_appointment18.mp3", "Okay butler, what do I have coming up next?", CALENDAR.name),
    ("get_next_appointment19.mp3", "Hey butler, can you tell me my next calendar event?", CALENDAR.name),
    ("get_next_appointment20.mp3", "Okay butler, what is the next event on my calendar?", CALENDAR.name),

    # Google Calendar list_this_weeks_appointments
    ("list_this_weeks_appointments0.mp3", "Hey butler, what events do I have this week?", CALENDAR.name),
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
    ("list_this_weeks_appointments11.mp3", "Hey butler, what are my events this week?", CALENDAR.name),
    ("list_this_weeks_appointments12.mp3", "Okay butler, list all my events for this week.", CALENDAR.name),
    ("list_this_weeks_appointments13.mp3", "Hey butler, can you show me my plans for the week?", CALENDAR.name),
    ("list_this_weeks_appointments14.mp3", "Okay butler, what are my appointments this week?", CALENDAR.name),
    ("list_this_weeks_appointments15.mp3", "Hey butler, what do I have planned for this week?", CALENDAR.name),
    ("list_this_weeks_appointments16.mp3", "Okay butler, what are my appointments for this week?", CALENDAR.name),
    ("list_this_weeks_appointments17.mp3", "Hey butler, show me my schedule for this week.", CALENDAR.name),
    ("list_this_weeks_appointments18.mp3", "Okay butler, what meetings do I have this week?", CALENDAR.name),
    ("list_this_weeks_appointments19.mp3", "Hey butler, can you list my events for this week?", CALENDAR.name),
    ("list_this_weeks_appointments20.mp3", "Okay butler, tell me what I have planned for the week.", CALENDAR.name),

    # Google Calendar delete_next_appointment
    ("delete_next_appointment0.mp3", "Hey butler, I would like to delete my next appointment.", CALENDAR.name),
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
    ("delete_next_appointment11.mp3", "Hey butler, I need to delete my next event.", CALENDAR.name),
    ("delete_next_appointment12.mp3", "Okay butler, cancel the next event in my calendar.", CALENDAR.name),
    ("delete_next_appointment13.mp3", "Hey butler, can you cancel my next scheduled meeting?", CALENDAR.name),
    ("delete_next_appointment14.mp3", "Okay butler, please remove my next calendar event.", CALENDAR.name),
    ("delete_next_appointment15.mp3", "Hey butler, delete the next thing on my calendar.", CALENDAR.name),
    ("delete_next_appointment16.mp3", "Hey butler, please delete my upcoming appointment.", CALENDAR.name),
    ("delete_next_appointment17.mp3", "Okay butler, can you cancel the next event?", CALENDAR.name),
    ("delete_next_appointment18.mp3", "Hey butler, I need to cancel my next meeting.", CALENDAR.name),
    ("delete_next_appointment19.mp3", "Okay butler, please remove the next appointment from my calendar.",
     CALENDAR.name),
    ("delete_next_appointment20.mp3", "Hey butler, delete my next scheduled event.", CALENDAR.name),

    # Google Calendar list_todays_appointments
    ("list_todays_appointments0.mp3", "Hey butler, what appointments do I have today?", CALENDAR.name),
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
    ("list_todays_appointments11.mp3", "Hey butler, what's on my schedule for today?", CALENDAR.name),
    ("list_todays_appointments12.mp3", "Okay butler, list today's meetings.", CALENDAR.name),
    ("list_todays_appointments13.mp3", "Hey butler, can you tell me today's appointments?", CALENDAR.name),
    ("list_todays_appointments14.mp3", "Okay butler, what's planned for today?", CALENDAR.name),
    ("list_todays_appointments15.mp3", "Hey butler, what do I have on my calendar for today?", CALENDAR.name),
    ("list_todays_appointments16.mp3", "Okay butler, list all my events for today.", CALENDAR.name),
    ("list_todays_appointments17.mp3", "Hey butler, tell me what I have on my schedule today.", CALENDAR.name),
    ("list_todays_appointments18.mp3", "Okay butler, what appointments do I have lined up today?", CALENDAR.name),
    ("list_todays_appointments19.mp3", "Hey butler, show me today's calendar events.", CALENDAR.name),
    ("list_todays_appointments20.mp3", "Okay butler, what's my agenda for today?", CALENDAR.name),

    # Google Calendar delete_all_appointments_today
    ("delete_all_appointments_today0.mp3", "Hey butler, delete all my appointments for today.", CALENDAR.name),
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
    ("delete_all_appointments_today11.mp3", "Hey butler, delete everything on my schedule today.", CALENDAR.name),
    ("delete_all_appointments_today12.mp3", "Okay butler, erase today's events.", CALENDAR.name),
    ("delete_all_appointments_today13.mp3", "Hey butler, remove all the meetings I have today.", CALENDAR.name),
    ("delete_all_appointments_today14.mp3", "Okay butler, delete all the scheduled events today.", CALENDAR.name),
    ("delete_all_appointments_today15.mp3", "Hey butler, cancel all today's appointments.", CALENDAR.name),
    ("delete_all_appointments_today16.mp3", "Hey butler, cancel all my events for today.", CALENDAR.name),
    ("delete_all_appointments_today17.mp3", "Okay butler, clear today's schedule.", CALENDAR.name),
    ("delete_all_appointments_today18.mp3", "Hey butler, please remove all today's appointments.", CALENDAR.name),
    ("delete_all_appointments_today19.mp3", "Okay butler, delete every appointment for today.", CALENDAR.name),
    ("delete_all_appointments_today20.mp3", "Hey butler, I need you to cancel all today's events.", CALENDAR.name),
]

bruh = [
    # Google Calendar am_i_free
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
    ("am_i_free10.mp3", "Hey butler, am I free in 48 hours?", CALENDAR.name),
    ("am_i_free11.mp3", "Okay butler, do I have anything on my schedule for next month at 3 PM?", CALENDAR.name),
    ("am_i_free12.mp3", "Hey butler, am I free in 10 days at 6 PM?", CALENDAR.name),
    ("am_i_free13.mp3", "Okay butler, do I have any appointments next Thursday at 7 AM?", CALENDAR.name),
    ("am_i_free14.mp3", "Hey butler, am I available this Saturday at 5 PM?", CALENDAR.name),
    ("am_i_free15.mp3", "Okay butler, do I have anything scheduled in one week at 2 PM?", CALENDAR.name),
    ("am_i_free16.mp3", "Hey butler, am I free next Wednesday at 8 AM?", CALENDAR.name),
    ("am_i_free17.mp3", "Okay butler, do I have any meetings in 15 days at 9 PM?", CALENDAR.name),
    ("am_i_free18.mp3", "Hey butler, am I free in three days at 10 AM?", CALENDAR.name),
    ("am_i_free19.mp3", "Okay butler, do I have anything planned this coming Friday at 11 PM?", CALENDAR.name),
    ("am_i_free20.mp3", "Hey butler, am I free in 12 hours?", CALENDAR.name),

    # Lecture get_lecture_content
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
    ("get_lecture_content10.mp3", "Hey butler, can you provide the last lecture transcript?", LECTURE.name),
    ("get_lecture_content11.mp3", "Okay butler, what was the main content of the previous lecture?", LECTURE.name),
    ("get_lecture_content12.mp3", "Hey butler, summarize the content of the last lecture for me.", LECTURE.name),
    ("get_lecture_content13.mp3", "Okay butler, I need the details from the last lecture.", LECTURE.name),
    ("get_lecture_content14.mp3", "Hey butler, what was the last lecture about?", LECTURE.name),
    ("get_lecture_content15.mp3", "Okay butler, tell me what the previous lecture covered.", LECTURE.name),
    ("get_lecture_content16.mp3", "Hey butler, I need to know what was discussed in the last lecture.", LECTURE.name),
    ("get_lecture_content17.mp3", "Okay butler, can you get me the last lecture content?", LECTURE.name),
    ("get_lecture_content18.mp3", "Hey butler, provide me the last lecture details.", LECTURE.name),
    ("get_lecture_content19.mp3", "Okay butler, what was the topic of the last lecture?", LECTURE.name),
    ("get_lecture_content20.mp3", "Hey butler, please get the previous lecture's transcript.", LECTURE.name)
]
#     ("get_lecture_content21.mp3", "Okay butler, what was the focus of the last lecture?", LECTURE.name),
#     ("get_lecture_content22.mp3", "Hey butler, I need the lecture notes from the last session.", LECTURE.name),
#     ("get_lecture_content23.mp3", "Okay butler, can you summarize the last lecture's content?", LECTURE.name)
# ]




def pytest_configure():
    pytest.one_off_test_data = one_off_test_data
    pytest.one_off_test = one_off_test


@pytest.fixture(scope="session")
def intent_manager_with_unknown_intent() -> IntentManager:
    intent_manager = IntentManager()
    intent_manager.add_intent(CALENDAR)
    intent_manager.add_intent(LECTURE)
    intent_manager.use_unknown_intent = True
    return intent_manager


@pytest.fixture(scope="session")
def llama2_client() -> LLMClient:
    return LLMClient(client=InferenceClient(AsrLlmConfig.llm_url))


@pytest.fixture(scope="session")
def few_shot_classifier(intent_manager_with_unknown_intent, llama2_client) -> BaseClassifier:
    return FewShotTextGenerationClassifier(
        llm_client=llama2_client,
        intent_manager=intent_manager_with_unknown_intent,
    )


@pytest.fixture(scope="session")
def ollama_classifier(intent_manager_with_unknown_intent) -> BaseClassifier:
    return OllamaClassifier(
        intent_manager_with_unknown_intent
    )


# ----------------------------- Report infrastructure -----------------------------

# Define a dictionary to store test results for each test function
test_results = {}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):  # noqa: ARG001
    # Get the test report for each test
    outcome = yield
    report = outcome.get_result()

    # Check if the test is finished
    if report.when == "call" and item.get_closest_marker("report_test"):
        # Get the test function name
        test_func_name = item.name.split("[")[0]

        # Initialize test results for the test function if not already done
        if test_func_name not in test_results:
            test_results[test_func_name] = []

        # Get the test result
        result = {
            "test_name": item.name,
            "input": item.funcargs.get("the_input"),
            "expected_output": item.funcargs.get("expected_output"),
            "expected": getattr(item, "_expected", None),
            "outcome": report.outcome,
            "output": getattr(item, "_output", None),  # Retrieve the output_intent from the item
            "llm_output": getattr(item, "_llm_output", None),  # Retrieve the output_intent from the item
        }
        test_results[test_func_name].append(result)

def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    report_dir = Path(os.getenv("PROJECT_DIR")) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"unit-test_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"

    report_lines = ["# Test Report", ""]

    for test_func_name, results in test_results.items():
        total = len(results)
        correct = sum(1 for result in results if result["output"] == result["expected"])
        accuracy = correct / total * 100 if total > 0 else 0

        report_lines.extend(
            [
                f"## {test_func_name}",
                f"**Total Tests:** {total}",
                f"**Correct:** {correct}",
                f"**Accuracy:** {accuracy:.2f}%",
                f"",
                #"### Detailed Results",
                #"",
            ],
        )

        # for i, result in enumerate(results):
        #     report_lines.extend(
        #         [
        #             f"#### Test Nr. {i + 1}",
        #             f"- **Test Name:** {result['test_name']}",
        #             f"- **Input:** {result['input']}",
        #             f"- **LLM Output:** {result['llm_output']}",
        #             f"- **Expected Intent:** {result['expected_output']}",
        #             f"- **Output Intent:** {result['output']}",
        #             f"- **Outcome:** {result['outcome']}",
        #             "",
        #         ],
        #     )

    with report_file.open("w") as f:
        f.write("\n".join(report_lines))


@pytest.fixture()
def capture_output_for_report(request):
    def setter(output, llm_output, expected):
        request.node._output = output  # noqa: SLF001
        request.node._llm_output = llm_output  # noqa: SLF001
        request.node._expected = expected

    request.node._output = None  # noqa: SLF001
    request.node._llm_output = None  # noqa: SLF001
    request.node._expected = None  # noqa: SLF001
    return setter
