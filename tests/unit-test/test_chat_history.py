import sys
from unittest import mock

import pytest
from huggingface_hub import InferenceClient

from src.asr_butler.asr_butler import ASRModule
from src.classifier.base_classifier import BaseClassifier, ClassifierResponse
from src.config.asr_llm_config import get_asr_llm_config
from src.history.chathistory import ChatHistory, Message, Role
from src.llm_client.llm_client import LLMClient
from src.prompt_generator.prompt_generator import PromptType
from src.state.state import InitialState, State

test_tuples = [
    # Questions, correct answers
    ("Hey Butler, What was the name of the first appointment we've created?", ["Project Meeting"]),
    ("Hey Butler, What was the name of the last appointment we've created?", ["Client Call"]),
    ("Hey Butler, How many appointments did we actually create an appointment?", ["4", "four"]),
    ("Hey Butler, How many times did I ask question regarding the lecture content?", ["2", "two", "twice"]),
    ("Hey Butler, How long the last appointment that we've created last", ["one", "1", "once"]),
]


@pytest.mark.parametrize("input, expected_outputs", test_tuples)
def test_chat_history_text_only(input, expected_outputs, chat_history, capture_output_for_report):
    sys.argv = [sys.argv[0]]
    arguments = get_asr_llm_config()

    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))

    # Initialize History
    history = ChatHistory()
    for i, _ in enumerate(chat_history):
        if i % 2 == 0:
            history.add_message(
                Message(
                    role=Role.USER,
                    text=chat_history[i]["content"],
                    classifier_response_level_1=ClassifierResponse(llm_response=chat_history[i + 1]["content"]),
                ),
            )
            history.add_message(Message(role=Role.ASSISTANT, text=chat_history[i + 1]["content"]))

    asr_module = ASRModule(
        args=arguments,
        llm_client=llm_client_,
        history=history,
        start_state=InitialState(llm_client=llm_client_, tts_client=None, use_function_caller=True),
        is_text_interface=True,
    )

    BaseClassifier.set_prompt_type(PromptType.FEW_SHOT_DETAILED)

    with mock.patch(
        "src.state.state.State.output",
        wrarps=State.output,
    ) as butler_output:
        asr_module.run_text_interface(
            [input],
        )

        butler_response = butler_output.call_args[1]["response"]
        if not any(correct_response in butler_response for correct_response in expected_outputs):
            pytest.fail(f"Butler Response: {butler_response}, Excepted indicators: {expected_outputs!s}")
        capture_output_for_report(output=butler_response, llm_output=None, expected=expected_outputs)
        # butler_outpe.assert_called_once()
        # assert called_function_name == expected_function_name

        #
