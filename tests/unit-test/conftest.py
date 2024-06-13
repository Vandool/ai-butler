# tests/unit-test/conftest.py
import datetime
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from src.classifier.base_classifier import BaseClassifier
from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.classifier.ollama_classifier import OllamaClassifier
from src.config.asr_llm_config import AsrLlmConfig
from src.intent.intent import CALENDAR, LECTURE
from src.intent.intent_manager import IntentManager
from src.llm_client.llm_client import LLMClient

# ----------------------------- Reusable Fixtures -----------------------------

load_dotenv()

one_off_test = ("get_next_appointment13.mp3", "Hey butler, whats up next?", CALENDAR.name),

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
]


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
        correct = sum(1 for result in results if result["output"])
        accuracy = correct / total * 100 if total > 0 else 0

        report_lines.extend(
            [
                f"## {test_func_name}",
                f"**Total Tests:** {total}",
                f"**Correct:** {correct}",
                f"**Accuracy:** {accuracy:.2f}%",
                "",
                "### Detailed Results",
                "",
            ],
        )

        for i, result in enumerate(results):
            report_lines.extend(
                [
                    f"#### Test Nr. {i + 1}",
                    f"- **Test Name:** {result['test_name']}",
                    f"- **Input:** {result['input']}",
                    f"- **LLM Output:** {result['llm_output']}",
                    f"- **Expected Intent:** {result['expected_output']}",
                    f"- **Output Intent:** {result['output']}",
                    f"- **Outcome:** {result['outcome']}",
                    "",
                ],
            )

    with report_file.open("w") as f:
        f.write("\n".join(report_lines))


@pytest.fixture()
def capture_output_for_report(request):
    def setter(output, llm_output):
        request.node._output = output  # noqa: SLF001
        request.node._llm_output = llm_output  # noqa: SLF001

    request.node._output = None  # noqa: SLF001
    request.node._llm_output = None  # noqa: SLF001
    return setter
