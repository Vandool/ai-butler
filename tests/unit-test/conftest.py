# tests/unit-test/conftest.py
import datetime
from pathlib import Path

import pytest
from sklearn.metrics import f1_score, recall_score

from src.classifier.few_shot_text_generation_classifier import FewShotTextGenerationClassifier
from src.classifier.zero_shot_classifier import ZeroShotClassifier
from src.config.asr_llm_config import AsrLlmConfig
from src.intent.intent_manager import CALENDAR, LECTURE, IntentManager

# ----------------------------- Reusable Fixtures -----------------------------


@pytest.fixture(scope="session")
def intent_manager_with_unknown_intent() -> IntentManager:
    intent_manager = IntentManager()
    intent_manager.add_intent(CALENDAR)
    intent_manager.add_intent(LECTURE)
    intent_manager.use_unknown_intent = True
    return intent_manager


@pytest.fixture(scope="session")
def few_shot_classifier(intent_manager_with_unknown_intent):
    classifier = FewShotTextGenerationClassifier(llm_url=AsrLlmConfig.llm_url)
    classifier.intent_manager = intent_manager_with_unknown_intent
    return classifier


@pytest.fixture(scope="session")
def zero_shot_classifier(intent_manager_with_unknown_intent):
    classifier = ZeroShotClassifier(model=AsrLlmConfig.zero_shot_model)
    classifier.intent_manager = intent_manager_with_unknown_intent
    return classifier


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
        }
        test_results[test_func_name].append(result)


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    report_dir = Path.cwd() / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"unit-test_{datetime.datetime.now()}.md"

    report_lines = ["# Test Report", ""]

    for test_func_name, results in test_results.items():
        total = len(results)
        correct = sum(1 for result in results if result["expected_output"] == result["output"])
        accuracy = correct / total * 100 if total > 0 else 0

        # Filter out results with None outputs
        valid_results = [result for result in results if result["output"] is not None]
        y_true = [result["expected_output"] for result in valid_results]
        y_pred = [result["output"] for result in valid_results]

        # Calculate F1 score and recall only if there are valid results
        if y_true and y_pred:
            f1 = f1_score(y_true, y_pred, average="macro")
            recall = recall_score(y_true, y_pred, average="macro")
        else:
            f1 = recall = 0.0

        report_lines.extend(
            [
                f"## {test_func_name}",
                f"**Total Tests:** {total}",
                f"**Correct:** {correct}",
                f"**Accuracy:** {accuracy:.2f}%",
                f"**F1 Score:** {f1:.2f}",
                f"**Recall:** {recall:.2f}",
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
    def setter(output):
        request.node._output = output  # noqa: SLF001

    request.node._output = None  # noqa: SLF001
    return setter
