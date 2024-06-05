from __future__ import annotations

import pytest

from src.intent.intent import CALENDAR, LECTURE, UNKNOWN
from src.prompt_generator.prompt_generator import PromptType

test_data = [
    # ("the_input_txt, the_input_audio, intent, function_name")
    # Google Calendar
    ("Add a new calendar event", CALENDAR.name),
    ("Set up a meeting for tomorrow", CALENDAR.name),
    ("When is my next scheduled event?", CALENDAR.name),
    ("Organize a team meeting", CALENDAR.name),
    ("Plan an event for next week", CALENDAR.name),
    ("Put a reminder for my doctor's appointment", CALENDAR.name),
    ("Book a time slot for my presentation", CALENDAR.name),
    ("Arrange a call with John", CALENDAR.name),
    ("What events do I have this week?", CALENDAR.name),
    ("Can you add a meeting to my calendar?", CALENDAR.name),
    ("Schedule a catch-up meeting", CALENDAR.name),
    ("Set a reminder for my yoga class", CALENDAR.name),
    ("Create an event at 3 PM", CALENDAR.name),
    ("When is my next meeting?", CALENDAR.name),
    ("Schedule a follow-up appointment", CALENDAR.name),
    # Lecture Translator
    ("Please translate these lecture slides", LECTURE.name),
    ("Turn the lecture audio into text", LECTURE.name),
    ("Can you summarize this lecture?", LECTURE.name),
    ("What are the key points of the lecture?", LECTURE.name),
    ("Generate a summary for today's lecture", LECTURE.name),
    ("Can you make flashcards from this lecture?", LECTURE.name),
    ("Transcribe the recorded lecture", LECTURE.name),
    ("Translate the lecture handouts", LECTURE.name),
    ("Provide a text version of the lecture", LECTURE.name),
    ("Create study notes from the lecture", LECTURE.name),
    ("Give me the main ideas from the lecture", LECTURE.name),
    ("What's the gist of the lecture?", LECTURE.name),
    ("Make a summary of the lecture notes", LECTURE.name),
    ("Highlight the important parts of the lecture", LECTURE.name),
    ("Convert the lecture video to text", LECTURE.name),
    # Unknown
    ("Zibber blorf zibber blorf", UNKNOWN.name),
    ("Why is the sky blue?", UNKNOWN.name),
    ("Who was the 16th president of the United States?", UNKNOWN.name),
    ("How many moons does Mars have?", UNKNOWN.name),
    ("Tell me a joke", UNKNOWN.name),
    ("What's the capital of France?", UNKNOWN.name),
    ("How does a computer work?", UNKNOWN.name),
    ("Explain quantum mechanics", UNKNOWN.name),
    ("What is the meaning of life?", UNKNOWN.name),
    ("What's the weather like today?", UNKNOWN.name),
    ("How to bake a cake?", UNKNOWN.name),
    ("What is the stock market?", UNKNOWN.name),
    ("Define artificial intelligence", UNKNOWN.name),
    ("How do airplanes fly?", UNKNOWN.name),
    ("What is photosynthesis?", UNKNOWN.name),
]


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


def handle_test(
    capture_output_for_report,
    expected_output,
    few_shot_classifier,
    the_input,
    prompt_type,
):
    response = few_shot_classifier.classify(input_text=the_input, prompt_type=prompt_type)
    if response.llm_response is not None:
        test_result = response.intent.name.lower() == expected_output.lower()
        capture_output_for_report(output=test_result, llm_output=response.llm_response)
        assert test_result
    else:
        capture_output_for_report(output=False, llm_output=response.llm_response)
        pytest.fail(msg=f"Simple classifier did not generate any intent for input {the_input}")
