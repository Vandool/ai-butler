# AI Butler

A voice-controlled AI assistant with automatic tool discovery and LLM-driven function calling — built from scratch without LangChain.

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Motivation & Design Philosophy

This project was built as part of the Dialogue Systems Praktikum at KIT (Summer 2024). Rather than reaching for LangChain or similar frameworks, we deliberately implemented the core patterns ourselves:

- **Intent classification** via LLM-powered few-shot and zero-shot strategies
- **Slot filling** through progressive, LLM-generated clarification questions
- **Function calling** with automatic tool discovery from decorated Python functions
- **Dialogue state management** using a state machine pattern

The goal was to prototype an assistant where **adding a new tool is as simple as writing a decorated function with a docstring** — and to deeply understand how these systems work under the hood.

## Architecture

```
                        ┌──────────────┐
  Audio / Text Input ──>│  ASR Module  │
                        └──────┬───────┘
                               │ transcript
                        ┌──────▼───────┐
                        │ State Machine│
                        │  (dialogue)  │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
      ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
      │ CalendarState│ │LectureState │ │FunctionCaller│
      │              │ │             │ │    State     │
      └──────┬───────┘ └──────┬──────┘ └──────┬───────┘
             │                │               │
             ▼                ▼               ▼
      Intent Classification (few-shot / zero-shot / function-caller)
                               │
                               ▼
                    ┌─────────────────────┐
                    │  @mark_intent tools │
                    │  auto-discovered via│
                    │  decorator + inspect│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │    Slot Filling     │
                    │ (if params missing) │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Function Execution  │──> LLM Response ──> TTS Output
                    └─────────────────────┘
```

### Key Design Patterns

| Pattern | Where | Purpose |
|---------|-------|---------|
| **State** | `src/state/state.py` | Dialogue flow — `InitialState` → domain-specific states |
| **Decorator Registry** | `@mark_intent` in `src/utils.py` | Automatic tool discovery via decorator + introspection |
| **Strategy** | `src/classifier/` | Swappable classifiers (zero-shot, few-shot, function-caller) |
| **Slot Filling** | `src/intent/slot_filler.py` | Progressive parameter collection via LLM-generated questions |

## How Tool Extensibility Works

This is the core design idea. To add a new tool to the assistant, you write a class with decorated methods:

```python
from src.utils import mark_intent

class WeatherAPI:
    @mark_intent
    def get_weather(self, city: str):
        """Get the current weather for a city.

        Examples:
            - What's the weather like in Berlin?
            - How's the weather in Munich today?
        """
        return weather_service.fetch(city)
```

Behind the scenes, the system:
1. **`@mark_intent`** flags the function for discovery
2. **`get_marked_functions_and_docstrings()`** introspects the module via `inspect`
3. **Docstring** is parsed into a description + few-shot examples for the classifier
4. **Function signature** is introspected to create `Slot` objects for parameter filling
5. **`IntentManager`** registers it as a classifiable intent
6. **`generate_classifier()`** wires everything into a ready-to-use classifier

No configuration files, no registration boilerplate — the decorator and docstring are the contract.

## Features

- **Voice activation** — wake word detection ("Ok Butler") with fuzzy matching
- **Real-time ASR** — streaming speech recognition via SSE (Server-Sent Events)
- **Google Calendar** — create, delete, list appointments; check availability
- **Lecture tools** — retrieve and interact with lecture content
- **Text-to-Speech** — response synthesis via Microsoft SpeechT5
- **Web UI** — real-time chat interface (Flask + SocketIO)
- **Conversation history** — context-aware responses across turns
- **Multiple input modes** — microphone (PyAudio), file/stream (FFmpeg), or text

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Llama 2 / Llama 3 via HuggingFace Inference API |
| ASR | KIT Lecture Translator (SSE streaming) |
| TTS | Microsoft SpeechT5 (HuggingFace) |
| Calendar | Google Calendar API v3 (service account) |
| Web UI | Flask + SocketIO |
| Audio | PyAudio / FFmpeg |
| Testing | pytest (parametrized tests) |
| Linting | ruff |

## Project Structure

```
ai_butler/
├── src/
│   ├── asr_butler/            # ASR processing and main dialogue loop
│   ├── classifier/            # Intent classifiers (few-shot, zero-shot, function-caller)
│   ├── codegen/               # Code generation from docstrings
│   ├── config/                # Configuration (CLI args, Google API, env vars)
│   ├── history/               # Chat history tracking
│   ├── intent/                # Intent definitions, manager, slot filling
│   ├── llm_client/            # HuggingFace Inference Client wrapper
│   ├── prompt_generator/      # Prompt templates (Llama 2/3 formats)
│   ├── state/                 # State machine (Initial, Calendar, Lecture, FunctionCaller)
│   ├── text2speech/           # Microsoft SpeechT5 TTS
│   ├── web_handler/           # External APIs (Google Calendar, Lecture Translator)
│   ├── web_interface/         # Flask + SocketIO web UI
│   └── utils.py               # @mark_intent decorator, JSON parsing, logging
├── webhandler/                # Selenium-based web automation (Lecture Translator, Zoom)
├── tests/
│   ├── unit-test/             # Unit tests (classifiers, chat history, functions)
│   └── e2e/                   # End-to-end tests
├── client.py                  # Main entry point — ASR + dialogue client
├── butler.yml                 # Conda environment definition
└── requirements.txt           # Python dependencies
```

## Getting Started

### 1. Create the environment

```bash
conda env create --name butler --file=butler.yml
conda activate butler
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```ini
# LLM endpoint
BUTLER_LLM_URL=http://localhost:8080

# Google Calendar (optional — needed for calendar tools)
GC_PRIVATE_KEY=...
GC_CLIENT_EMAIL=...
GC_PROJECT_ID=...
GC_PRIVATE_KEY_ID=...
GC_CLIENT_ID=...
GC_CALENDAR_ID=...
```

### 3. Run

```bash
# Audio mode (requires microphone)
python client.py --token <YOUR_TOKEN> --llm <LLM_URL> -a <AUDIO_DEVICE_ID>

# Text mode
python src/my_text_client.py
```

## Prototype Limitations & Known Trade-offs

> This is a university prototype built in ~3 months by a team of 3. The following are conscious trade-offs or areas that would need attention for production use:

- **Error handling is minimal** — some bare `except:` blocks in client code, and `sys.exit(1)` on HTTP errors. Production would need retry logic, circuit breakers, and typed exception handling.
- **Some hardcoded configuration** — a few URLs and ports (e.g. the web UI callback at `localhost:6969`) are hardcoded rather than fully configurable. The `AsrLlmConfig` dataclass covers most settings but not all.
- **No authentication on the web UI** — the Flask-SocketIO interface has no auth layer.
- **Logging is inconsistent** — mix of `print()` and structured logging via `CustomLogger`. Would unify under structured logging (e.g. `structlog`) in production.
- **Prompt templates are model-specific** — prompts use Llama 2/3 chat format (`[INST]`/`<</SYS>>`). Switching models requires updating prompt templates.
- **No CI/CD** — tests exist but there's no automated pipeline.
- **Slot filling is sequential** — asks for one parameter at a time rather than extracting multiple slots from a single utterance.

## What I'd Do Differently

Looking back with more experience, here's what I'd change:

- **Structured logging from day one** — consistent observability across all modules
- **Prompt abstraction layer** — decouple prompt format from model, enabling model portability
- **Error boundaries per state** — each state should gracefully handle failures without crashing the dialogue loop
- **Integration tests with mocked LLM** — deterministic testing of the dialogue pipeline
- **Dependency injection** — for the LLM client and external APIs, making the system more testable
- **OpenAPI-style tool definitions** — more robust than docstring parsing, with schema validation

## Contributors

- **Arvand Kaveh** ([@Vandool](https://github.com/Vandool)) — primary contributor (architecture, state machine, tool extensibility, slot filling, testing)
- Namid Marxen — calendar integration, web handler
- Daniel Boesch — contributions

Course supervised by Sai Koneru at KIT.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
