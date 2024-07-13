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
from src.history.chathistory import ChatHistory
from src.llm_client.llm_client import LLMClient
from huggingface_hub import InferenceClient

from src.prompt_generator.prompt_generator import PromptType
from src.state.state import InitialState, State, CalendarState, FunctionCallerState
from unittest import mock

dialog_test_data = pytest.dialog_test_data[5:6]
# one_off_test_data = [pytest.one_off_test_data[1]]
# one_off_test_data = pytest.one_off_test


@pytest.mark.parametrize("inputs", dialog_test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_text_only_few_shot(inputs, capture_output_for_report):
    test_text_only(inputs, PromptType.FEW_SHOT_DETAILED, capture_output_for_report)


@pytest.mark.parametrize("inputs", dialog_test_data)
@pytest.mark.report_test()  # Custom marker to include this test in the report
def test_audio_few_shot(inputs, capture_output_for_report):
    test_with_audio(inputs, PromptType.FEW_SHOT_DETAILED, capture_output_for_report)


def start_thread(asr_module):
    time.sleep(1)
    asr_module.send_session()


def test_with_audio(inputs, prompt_type, capture_output_for_report):
    input_files = file_names = [test[0][0] for test in inputs]

    expected_function_name = re.match(r"([a-zA-Z_]+)\d+_\d+\.mp3$",  inputs[0][0]).group(1)

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

        called_function_name = function_name_helper_wrapper.call_args.args[0]
        capture_output_for_report(output=called_function_name, llm_output=None, expected=expected_function_name)
        function_name_helper_wrapper.assert_called_once()
        assert called_function_name == expected_function_name


def test_text_only(inputs, prompt_type, capture_output_for_report):
    input_texts = [part[1] for part in inputs]

    expected_function_name = re.match(r"([a-zA-Z_]+)\d+_\d+\.mp3$",  inputs[0][0]).group(1)

    sys.argv = [sys.argv[0]]
    arguments = get_asr_llm_config()

    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))
    asr_module = ASRModule(
        args=arguments,
        llm_client=llm_client_,
        history=ChatHistory(),
        start_state=InitialState(llm_client=llm_client_, tts_client=None, use_function_caller=True)
    )

    BaseClassifier.set_prompt_type(prompt_type)

    with (
        mock.patch('src.state.state.FunctionCallerState._function_name_helper', wrarps=FunctionCallerState._function_name_helper) as function_name_helper_wrapper
    ):
        asr_module.run_text_interface(
            input_texts,
        )

        called_function_name = function_name_helper_wrapper.call_args.args[0]
        capture_output_for_report(output=called_function_name, llm_output=None, expected=expected_function_name)
        function_name_helper_wrapper.assert_called_once()
        assert called_function_name == expected_function_name

