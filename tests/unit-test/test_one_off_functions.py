import os
import pathlib
import sys
import time
import pytest
import re

from threading import Thread
from src.asr_butler.asr_butler import ASRModule
from src.classifier.base_classifier import BaseClassifier
from src.config.asr_llm_config import get_asr_llm_config
from src.llm_client.llm_client import LLMClient
from huggingface_hub import InferenceClient

from src.prompt_generator.prompt_generator import PromptType
from src.state.state import InitialState, State, CalendarState
from unittest import mock

# one_off_test_data = pytest.one_off_test_data
# one_off_test_data = [pytest.one_off_test_data[1]]
one_off_test_data = pytest.one_off_test


@pytest.mark.parametrize("the_input, input_text, _", one_off_test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_text_only_few_shot(the_input, input_text,_, capture_output_for_report):
    test_text_only(the_input, input_text, PromptType.FEW_SHOT_DETAILED, capture_output_for_report)


@pytest.mark.parametrize("the_input, input_text, intent_name", one_off_test_data)
def test_audio_few_shot(the_input, input_text, intent_name, capture_output_for_report):
    test_with_audio(the_input, input_text, PromptType.FEW_SHOT_DETAILED, capture_output_for_report)


def start_thread(asr_module):
    time.sleep(1)
    asr_module.send_session()


def test_with_audio(input_file, input_text, prompt_type, capture_output_for_report):
    function_name = re.match(r"([a-zA-Z_]+)(\d+)\.mp3$", input_file).group(1)

    sys.argv = [sys.argv[0]]
    arguments = get_asr_llm_config()

    arguments.input = "ffmpeg"
    test_dir = pathlib.Path(os.getenv("PROJECT_DIR")) / "tests" / "test_data"
    arguments.ffmpeg_input = test_dir / input_file
    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))
    asr_module = ASRModule(
        args=arguments,
        llm_client=llm_client_,
        history=None,
        start_state=InitialState(llm_client=llm_client_, tts_client=None)
    )

    BaseClassifier.set_prompt_type(prompt_type)

    asr_module.set_graph()

    t = Thread(target=start_thread, args=(asr_module,))
    t.daemon = True
    t.start()

    with (
        mock.patch('src.state.state.CalendarState._function_name_helper',
                   wrarps=CalendarState._function_name_helper) as function_name_helper_wrapper
    ):
        start_time = time.monotonic()
        asr_module.read_text(start_time, True)

        function_name_helper_wrapper.assert_called_once()
        assert function_name_helper_wrapper.call_args.args[0] == function_name


def test_text_only(input_file, input_text, prompt_type, capture_output_for_report):
    function_name = re.match(r"([a-zA-Z_]+)(\d+)\.mp3$", input_file).group(1)

    sys.argv = [sys.argv[0]]
    arguments = get_asr_llm_config()

    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))
    asr_module = ASRModule(
        args=arguments,
        llm_client=llm_client_,
        history=None,
        start_state=InitialState(llm_client=llm_client_, tts_client=None)
    )

    BaseClassifier.set_prompt_type(prompt_type)

    with (
        mock.patch('src.state.state.CalendarState._function_name_helper', wrarps=CalendarState._function_name_helper) as function_name_helper_wrapper
    ):
        asr_module.run_text_interface(
            [
                input_text
            ],
        )

        function_name_helper_wrapper.assert_called_once()
        test_result = function_name_helper_wrapper.call_args.args[0] == function_name
        capture_output_for_report(output=test_result, llm_output=function_name)
        assert test_result

