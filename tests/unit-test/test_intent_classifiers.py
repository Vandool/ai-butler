from __future__ import annotations

import pytest

from src.classifier.base_classifier import BaseClassifier
from src.intent.intent import CALENDAR, LECTURE, UNKNOWN
from src.prompt_generator.prompt_generator import PromptType

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

test_data = test_data + [(b, c) for _, b, c in pytest.one_off_test_data]


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
def test_ollama_text_generation_one_shot(
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
        prompt_type=PromptType.ONE_SHOT_PER_CLASS_DETAILED,

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
    # Can be done in both ways
    # 1) Global setter
    # 2) The global setters value can be overwritten when the parameter is given to the .classify() method
    BaseClassifier.set_prompt_type(prompt_type=prompt_type)
    response = few_shot_classifier.classify(input_text=the_input)
    if response.llm_response is not None:
        test_result = response.intent.name.lower() == expected_output.lower()
        capture_output_for_report(output=test_result, llm_output=response.llm_response)
        assert test_result
    else:
        capture_output_for_report(output=False, llm_output=response.llm_response)
        pytest.fail(msg=f"Simple classifier did not generate any intent for input {the_input}")
