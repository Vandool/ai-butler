from __future__ import annotations

import os
import pathlib
import sys
import time
from threading import Thread

import pytest

from src.config import config_utils
from src.intent.intent import CALENDAR, LECTURE, UNKNOWN
from src.prompt_generator.prompt_generator import PromptType
from src.asr_butler.asr_butler import ASRModule
from src.config.asr_llm_config import get_asr_llm_config, AsrLlmConfig
from src.llm_client.llm_client import LLMClient
from huggingface_hub import InferenceClient
from src.state.state import InitialState, State

one_shot_test_data = [
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

    # Google Calendar list_this_weeks_appointments
    ("list_this_weeks_appointments0.mp3", "Hey butler, what events do I have this week?", CALENDAR.name),
    ("list_this_weeks_appointments1.mp3", "Hey butler, what commitments do I have this week?", CALENDAR.name),
    ("list_this_weeks_appointments2.mp3", "Okay butler, show me all my appointments for this week.", CALENDAR.name),
    ("list_this_weeks_appointments3.mp3", "Hey butler, what appointments do I have lined up this week?", CALENDAR.name),
    ("list_this_weeks_appointments4.mp3", "Okay butler, list my schedule for the current week.", CALENDAR.name),
    ("list_this_weeks_appointments5.mp3", "Hey butler, can you tell me my meetings for this week?", CALENDAR.name),
    ("list_this_weeks_appointments6.mp3", "Okay butler, I need to know all the appointments I have this week.", CALENDAR.name),
    ("list_this_weeks_appointments7.mp3", "Hey butler, what are my plans for this week?", CALENDAR.name),
    ("list_this_weeks_appointments8.mp3", "Okay butler, please list my engagements for this week.", CALENDAR.name),
    ("list_this_weeks_appointments9.mp3", "Hey butler, tell me my schedule for this week.", CALENDAR.name),
    ("list_this_weeks_appointments10.mp3", "Okay butler, what do I have scheduled this week?", CALENDAR.name),

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
]

test_data = [
    # Google Calendar general
    ("calendar1.mp3", "Add a new calendar event", CALENDAR.name),
    ("calendar2.mp3", "Set up a meeting for tomorrow", CALENDAR.name),
    ("calendar3.mp3", "Organize a team meeting", CALENDAR.name),
    ("calendar4.mp3", "Plan an event for next week", CALENDAR.name),
    ("calendar5.mp3", "Put a reminder for my doctor's appointment", CALENDAR.name),
    ("calendar6.mp3", "Book a time slot for my presentation", CALENDAR.name),
    ("calendar7.mp3", "Arrange a call with John", CALENDAR.name),
    ("calendar8.mp3", "Can you add a meeting to my calendar?", CALENDAR.name),
    # Unknown
    ("unknown1.mp3", "Zibber blorf zibber blorf", UNKNOWN.name),
    ("unknown2.mp3", "Why is the sky blue?", UNKNOWN.name),
    ("unknown3.mp3", "Who was the 16th president of the United States?", UNKNOWN.name),
    ("unknown4.mp3", "How many moons does Mars have?", UNKNOWN.name),
    ("unknown5.mp3", "Tell me a joke", UNKNOWN.name),
    ("unknown6.mp3", "What's the capital of France?", UNKNOWN.name),
    ("unknown7.mp3", "How does a computer work?", UNKNOWN.name),
    ("unknown8.mp3", "Explain quantum mechanics", UNKNOWN.name),
    ("unknown9.mp3", "What is the meaning of life?", UNKNOWN.name),
    ("unknown10.mp3", "What's the weather like today?", UNKNOWN.name),
    # Lecture Translator general
    ("lecture1.mp3", "Please translate these lecture slides", LECTURE.name),
    ("lecture2.mp3", "Turn the lecture audio into text", LECTURE.name),
    ("lecture3.mp3", "Can you summarize this lecture?", LECTURE.name),
    ("lecture4.mp3", "What are the key points of the lecture?", LECTURE.name),
    ("lecture5.mp3", "Generate a summary for today's lecture", LECTURE.name),
    ("lecture6.mp3", "Can you make flashcards from this lecture?", LECTURE.name),
    ("lecture7.mp3", "Transcribe the recorded lecture", LECTURE.name),
    ("lecture8.mp3", "Translate the lecture handouts", LECTURE.name),
    ("lecture9.mp3", "Provide a text version of the lecture", LECTURE.name),
    ("lecture10.mp3", "Create study notes from the lecture", LECTURE.name),
]
# Remove audio_file for current implementation of tests
test_data = [(b, c) for _, b, c in test_data]


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_zero_shot(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.ZERO_SHOT,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_zero_shot_detailed(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.ZERO_SHOT_DETAILED,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_one_shot_detailed(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.ONE_SHOT_PER_CLASS_DETAILED,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_one_shot(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.ONE_SHOT_PER_CLASS,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_few_shot_detailed(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.FEW_SHOT_DETAILED,
    )


one_shot_test_data = [one_shot_test_data[1]]


def start_thread(asr_module):
    time.sleep(1)
    asr_module.send_session()


@pytest.mark.parametrize("the_input,_ , expected_output", one_shot_test_data)
def test_audio_few_shot_classifier(the_input, _, expected_output, capture_output_for_report, few_shot_classifier):
    sys.argv = [sys.argv[0]]
    arguments = get_asr_llm_config()

    # arguments.token = config_utils.get_mandatory_env_variable("BUTLER_USER_TOKEN")
    # arguments.show_on_website = False
    # arguments.api = "webapi"
    # arguments.asr_properties = {}
    # arguments.mt_properties = {}
    # arguments.prep_properties = {}
    arguments.input = "ffmpeg"
    test_dir = pathlib.Path(os.getenv("PROJECT_DIR")) / "tests" / "test_data"
    arguments.ffmpeg_input = test_dir / the_input
    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))
    asr_module = ASRModule(
        args=arguments,
        llm_client=llm_client_,
        history=None,
        start_state=InitialState(llm_client=llm_client_, tts_client=None)
    )

    asr_module.set_graph()

    t = Thread(target=start_thread, args=(asr_module,))
    t.daemon = True
    t.start()

    start_time = time.monotonic()
    asr_module.read_text(start_time)

    # Get the ASR output from the transcript buffer
    # TODO: Add mocks here
    asr_output = asr_module.transcript_buffer.strip()

    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        asr_output,
        prompt_type=PromptType.ZERO_SHOT_DETAILED,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_few_shot_text_generation_classifier_few_shot(
        the_input,
        expected_output,
        capture_output_for_report,
        few_shot_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type=PromptType.FEW_SHOT,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_ollama_text_generation_classifier_zero_shot(
        the_input,
        expected_output,
        capture_output_for_report,
        ollama_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        ollama_classifier,
        the_input,
        prompt_type=PromptType.ZERO_SHOT,
    )


@pytest.mark.parametrize("the_input, expected_output", test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_ollama_text_generation_few_shot(
        the_input,
        expected_output,
        capture_output_for_report,
        ollama_classifier,
):
    handle_test(
        capture_output_for_report,
        expected_output,
        ollama_classifier,
        the_input,
        prompt_type=PromptType.FEW_SHOT_DETAILED,
    )


def handle_test(
        capture_output_for_report,
        expected_output,
        few_shot_classifier,
        the_input,
        prompt_type: PromptType | None = None,
):
    response = few_shot_classifier.classify(input_text=the_input, prompt_type=prompt_type)
    if response.llm_response is not None:
        test_result = response.intent.name.lower() == expected_output.lower()
        capture_output_for_report(output=test_result, llm_output=response.llm_response)
        assert test_result
    else:
        capture_output_for_report(output=False, llm_output=response.llm_response)
        pytest.fail(msg=f"Simple classifier did not generate any intent for input {the_input}")
