from __future__ import annotations

import argparse
from dataclasses import dataclass, field

from dotenv import load_dotenv

from src.config import config_utils

load_dotenv()


@dataclass
class AsrLlmConfig:
    token: str
    llm_url: str = "https://5114-141-3-25-29.ngrok-free.app"
    zero_shot_model: str = "facebook/bart-large-mnli"
    url: str = "https://lt2srv-backup.iar.kit.edu"
    input: str = "portaudio"
    print_level: int = 0
    output_file: str = None
    audio_device: int = 0
    ffmpeg_input: str = None
    ffmpeg_pre: str = None
    ffmpeg_post: str = None
    volume: float = 1.0
    ffmpeg_speed: float = 1.0
    upload_video: bool = False
    translate_link: bool = False
    save_path: str = ""
    no_logging: bool = False
    run_mt: str = None
    asr_properties: dict = field(default_factory=dict)
    no_textsegmenter: bool = False
    textseg_properties: dict = field(default_factory=dict)
    use_error_correction: bool = False
    mt_properties: dict = field(default_factory=dict)
    use_prep: bool = False
    use_summarize: bool = False
    use_postproduction: bool = False
    prep_properties: dict = field(default_factory=dict)
    tts_properties: dict = field(default_factory=dict)
    video_properties: dict = field(default_factory=dict)
    show_on_website: bool = field(default_factory=dict)
    website_title: str = "Audioclient"
    meta: str = ""
    access: str = ""
    run_scheduler: bool = False
    timeout: int = None
    titanic_ip: str = None
    run_tts: str = None
    generate_video: str = None
    save_video: str = None
    summarize: bool = False
    speaker_diarization: bool = False
    absolute_timestamps: bool = False
    memory_words: list = None
    api: str = None
    list_available_languages: bool = False
    list_active_sessions: bool = False
    buffer_size: int = 4096  # Default buffer size
    chunk_size: int = 1024  # Default chunk size
    default_llm_inference_seed: bool | None = None


def get_asr_llm_config() -> AsrLlmConfig:
    args = parse_arguments()

    token_ = args.token or config_utils.get_mandatory_env_variable("BUTLER_USER_TOKEN")
    return AsrLlmConfig(
        token=token_,
        llm_url=args.llm_url or config_utils.get_env_variable_with_default("BUTLER_LLM_URL", AsrLlmConfig.llm_url),
        zero_shot_model=args.zero_shot_model
        or config_utils.get_env_variable_with_default("BUTLER_ZERO_SHOT_MODEL", AsrLlmConfig.zero_shot_model),
        default_llm_inference_seed=config_utils.get_env_variable_with_default(
            "DEFAULT_LLM_INFERENCE_SEED",
            AsrLlmConfig.default_llm_inference_seed,
        ),
        url=args.url,
        input=args.input,
        print_level=args.print_level,
        output_file=args.output_file,
        audio_device=args.audio_device,
        ffmpeg_input=args.ffmpeg_input,
        ffmpeg_pre=args.ffmpeg_pre,
        ffmpeg_post=args.ffmpeg_post,
        volume=args.volume,
        ffmpeg_speed=args.ffmpeg_speed,
        upload_video=args.upload_video,
        translate_link=args.translate_link,
        save_path=args.save_path,
        no_logging=args.no_logging,
        run_mt=args.run_mt,
        asr_properties=dict(args.asr_properties) if args.asr_properties else {},
        no_textsegmenter=args.no_textsegmenter,
        textseg_properties=dict(args.textseg_properties) if args.textseg_properties else {},
        use_error_correction=args.use_error_correction,
        mt_properties=dict(args.mt_properties) if args.mt_properties else {},
        use_prep=args.use_prep,
        use_summarize=args.use_summarize,
        use_postproduction=args.use_postproduction,
        prep_properties=dict(args.prep_properties) if args.prep_properties else {},
        tts_properties=dict(args.tts_properties) if args.tts_properties else {},
        video_properties=dict(args.video_properties) if args.video_properties else {},
        show_on_website=args.show_on_website,
        website_title=args.website_title,
        meta=args.meta,
        access=args.access,
        run_scheduler=args.run_scheduler,
        timeout=args.timeout,
        titanic_ip=args.titanic_ip,
        run_tts=args.run_tts,
        generate_video=args.generate_video,
        save_video=args.save_video,
        summarize=args.summarize,
        speaker_diarization=args.speaker_diarization,
        absolute_timestamps=args.absolute_timestamps,
        memory_words=args.memory_words,
        api="webapi" if token_ is not None else "ltapi",
        list_available_languages=args.list_available_languages,
        list_active_sessions=args.list_active_sessions,
        buffer_size=args.buffer_size,
        chunk_size=args.chunk_size,
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--llm-url", help="URL of the language model", default=None)
    parser.add_argument("--token", help="Web API access token for authentication", default=None)
    parser.add_argument("--zero-shot-model", help="Zero-shot model name", default=None)
    parser.add_argument(
        "-u",
        "--url",
        default="https://lt2srv-backup.iar.kit.edu",
        help="Where to send the audio to",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Which input type should be used",
        choices=["portaudio", "ffmpeg", "link"],
        default="portaudio",
    )
    parser.add_argument(
        "--print_level",
        help=(
            "Specify the verbosity level of printed output: "
            "0 - Only print hypotheses; "
            "1 - Print all received data; "
            "2 - Print all received data with timestamps (seconds since session start)."
        ),
        type=int,
        default=0,
    )
    parser.add_argument(
        "--list-available-languages",
        help="List available languages of mediator",
        action="store_true",
    )
    parser.add_argument("--list-active-sessions", help="List active session on mediator", action="store_true")
    parser.add_argument(
        "--output-file",
        help="Path to the file to save the output translations",
        type=str,
        default=None,
    )

    # ===================== PyAudio/Portaudio =====================
    parser.add_argument("-L", "--list", help="Pyaudio. List audio available audio devices", action="store_true")
    parser.add_argument("-a", "--audio_device", help="Pyaudio. Index of audio device to use", default=-1, type=int)
    parser.add_argument(
        "-ch",
        "--audiochannel",
        help="Index of audio channel to use (first channel = 1)",
        type=int,
        default=None,
    )
    parser.add_argument("--chunk_size", help="Chunk size for audio input", type=int, default=1024)
    parser.add_argument("--buffer_size", help="Buffer size for audio input", type=int, default=4096)

    # ===================== Ffmpeg =====================
    parser.add_argument("-f", "--ffmpeg-input", help="Input file/address that will be given to ffmpeg", type=str)
    parser.add_argument(
        "--ffmpeg-pre",
        help="Ffmpeg options inserted before input parameter (-f). Don't forget to escape via string so this will be "
        "one single parameter.",
        type=str,
    )
    parser.add_argument(
        "--ffmpeg-post",
        help="Ffmpeg options inserted after input parameter (-f). Don't forget to escape via string so this will be "
        "one single parameter.",
        type=str,
    )
    parser.add_argument("--volume", help="Adjust the volume via ffmpeg", type=float, default=1.0)
    parser.add_argument(
        "--ffmpeg-speed",
        help="Set ffmpeg sending speed, -1 is infinite speed",
        type=float,
        default=1.0,
    )

    parser.add_argument("--upload-video", help="Whether to upload the full ffmpeg input video", action="store_true")
    parser.add_argument("--translate_link", help="Whether to translate a link", action="store_true")
    parser.add_argument("--save-path", help="Where to store the session in the archive", type=str, default="")

    # ===================== Properties =====================
    parser.add_argument("--no-logging", help="Do not log the session on the server", action="store_true")
    parser.add_argument(
        "--run-mt",
        help='Run a MT model in addition to ASR, comma separated string of output languages, e.g. "en-de,en-fr"',
        default=None,
    )
    parser.add_argument(
        "--asr-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="asr_properties",
        help="Used ASR properties, e.g. --asr-kv version=online --asr-kv segmenter=VAD --asr-kv "
        "stability_detection=False for online or --asr-kv version=offline --asr-kv segmenter=None for offline",
    )
    parser.add_argument("--no-textsegmenter", help="Set this to not use a textsegmenter", action="store_true")
    parser.add_argument("--textseg-kv", action="append", type=lambda kv: kv.split("="), dest="textseg_properties")
    parser.add_argument("--use-error-correction", action="store_true")
    parser.add_argument(
        "--mt-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="mt_properties",
        help="Used MT properties, e.g. --mt-kv mode=SendStable --mt-kv mt_server=http://URL:PORT/SOMETHING",
    )
    parser.add_argument(
        "--use-prep",
        help="Run a preprocessing model (e.g. noise filtering) before ASR",
        action="store_true",
    )
    parser.add_argument("--use-summarize", help="Use summarization", action="store_true")
    parser.add_argument("--use-postproduction", help="Use postproduction", action="store_true")
    parser.add_argument(
        "--prep-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="prep_properties",
        help="Used prep properties",
    )
    parser.add_argument(
        "--tts-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="tts_properties",
        help="Used TTS properties",
    )
    parser.add_argument(
        "--video-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="video_properties",
        help="Used video properties",
    )
    parser.add_argument(
        "--show-on-website",
        help="Whether to show this session on the website",
        action="store_true",
    )
    parser.add_argument(
        "--website-title",
        help="Which title is shown on the website",
        type=str,
        default="Audioclient",
    )
    parser.add_argument("--meta", help="Meta information for website title", type=str, default="")
    parser.add_argument("--access", help="Access information for website title", type=str, default="")
    parser.add_argument("--run-scheduler", help="Whether to run scheduler", action="store_true")
    parser.add_argument(
        "--timeout",
        help="After how many seconds to stop the sending of audio, None: No timeout",
        type=int,
        default=None,
    )
    parser.add_argument("--titanic-ip", default=None)
    parser.add_argument(
        "--run-tts",
        help='Run a TTS model, comma separated string of output languages, e.g. "en,de"',
        default=None,
    )
    parser.add_argument(
        "--generate-video",
        help='Run a video generation model, comma separated string of output languages, e.g. "en,de"',
        default=None,
    )
    parser.add_argument(
        "--save-video",
        help="File to save the generated video locally on this PC",
        default=None,
        type=str,
    )
    parser.add_argument("--summarize", help="Adds a summarizer after text segmentation.", action="store_true")
    parser.add_argument("--speaker-diarization", help="TODO", action="store_true")
    parser.add_argument("--absolute-timestamps", help="Returns absolute timestamps", action="store_true")
    parser.add_argument(
        "--memory-words",
        help="Words used in the memory-enhanced ASR model",
        nargs="+",
        default=None,
    )

    return parser.parse_args()
