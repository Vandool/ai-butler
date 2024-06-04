import argparse
import base64
import copy
import json
import os
import socket
import sys
import time
from datetime import datetime
from threading import Thread

import requests
from sseclient import SSEClient

from src import utils
from src.pythonrecordingclient import BugException
from webhandler.webutils import check_status_code, return_json

logger = utils.get_logger("Client")


def verify_chunk_size(value: str | int) -> int:
    try:
        val: int = int(value)
        assert val > 0
    except:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return val


def get_audio_input(args):
    if args.input == "link":
        return args.ffmpeg_input
    if args.input == "portaudio":
        from src.pythonrecordingclient.pyaudioStreamAdapter import PortaudioStream

        logger.info("Using portaudio as input. If you want to use ffmpeg specify '-i ffmpeg'.")
        stream_adapter = PortaudioStream()
        input = args.audiodevice
        if args.list:
            stream_adapter.print_all_devices()
        if args.audiodevice < 0:
            logger.info(
                "The portaudio backend requires the '-a' parameter. Run python client.py -L to see the available audio devices.",
            )
            sys.exit(1)
    elif args.input == "ffmpeg":
        from src.pythonrecordingclient.ffmpegStreamAdapter import FfmpegStream

        stream_adapter = FfmpegStream(
            pre_input=args.ffmpeg_pre,
            post_input=args.ffmpeg_post,
            volume=args.volume,
            repeat_input=False,
            ffmpeg_speed=args.ffmpeg_speed,
        )
        input = args.ffmpeg_input
        if input is None:
            logger.info("The ffmpeg backend requires an url/file via the '-f' parameter")
            sys.exit(1)
        elif not os.path.isfile(input) and not input.startswith("rtsp"):
            logger.info("File", input, "does not exist")
            sys.exit(1)
    else:
        raise BugException()

    stream_adapter.set_input(input)

    # if args.audiochannel is not None:
    #    if not isinstance(stream_adapter, PortaudioStream):
    #        print("Audio channels are currently only supported with portaudio TODO")
    #        exit(1)
    #    stream_adapter.set_audio_channel_filter(args.audiochannel)

    return stream_adapter


def send_start(url, sessionID, streamID, show_on_website, save_path, website_title, meta, access, api, token):
    logger.info("Start sending audio")
    data = {"controll": "START"}
    if show_on_website:
        data["type"] = "lecture"
        data["name"] = website_title
    if meta:
        data["meta"] = meta
    if access:
        data["access"] = access
    if save_path != "":
        data["directory"] = save_path
    info = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if info.status_code != 200:
        logger.error(info.status_code, info.text)
        logger.error("ERROR in starting session")
        sys.exit(1)


def send_audio(
    last_end,
    audio_source,
    url,
    sessionID,
    streamID,
    api,
    token,
    raise_interrupt=True,
    absolute_timestamps=False,
):
    chunk = audio_source.read()
    chunk = audio_source.chunk_modify(chunk)
    if raise_interrupt and len(chunk) == 0:
        raise KeyboardInterrupt
    if not absolute_timestamps:
        s = last_end
    else:
        s = time.time()
    e = s + len(chunk) / 32000
    data = {"b64_enc_pcm_s16le": base64.b64encode(chunk).decode("ascii"), "start": s, "end": e}
    res = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if res.status_code != 200:
        logger.error(res.status_code, res.text)
        logger.error("ERROR in sending audio")
        sys.exit(1)
    return e


def send_video(videopath, url, sessionID, streamID, api, token):
    video = open(videopath, "rb").read()
    data = {"b64_enc_audio": base64.b64encode(video).decode("ascii")}
    res = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if res.status_code != 200:
        logger.error(res.status_code, res.text)
        logger.error("ERROR in sending video")
        sys.exit(1)
    logger.info("Video successfully sent.")


def send_link(videopath, url, sessionID, streamID, api, token):
    data = {"url": videopath}
    res = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if res.status_code != 200:
        logger.error(res.status_code, res.text)
        logger.error("ERROR in sending video")
        sys.exit(1)
    logger.info("Video successfully sent.")


def send_memory(url, sessionID, streamID, api, token, memory_words):
    data = {"memory_words": json.dumps(memory_words)}
    res = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if res.status_code != 200:
        logger.error(res.status_code, res.text)
        logger.error("ERROR in sending memory")
        sys.exit(1)
    logger.info("Memory successfully sent.")


def send_end(url, sessionID, streamID, api, token):
    logger.info("Sending END.")
    data = {"controll": "END"}
    res = requests.post(
        url + "/" + api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": token},
    )
    if res.status_code != 200:
        logger.error(res.status_code, res.text)
        logger.error("ERROR in sending END message")
        sys.exit(1)


def send_session(
    url,
    sessionID,
    streamID,
    audio_source,
    show_on_website,
    upload_video,
    translate_link,
    save_path,
    website_title,
    meta,
    access,
    timeout,
    api,
    token,
    absolute_timestamps,
    memory_words,
):
    try:
        start_time = time.time()
        send_start(url, sessionID, streamID, show_on_website, save_path, website_title, meta, access, api, token)
        if memory_words is not None:
            send_memory(url, sessionID, streamID, api, token, memory_words)
        if translate_link:
            send_link(audio_source, url, sessionID, streamID, api, token)
        elif not upload_video:
            last_end = 0
            while timeout is None or time.time() - start_time < timeout:
                last_end = send_audio(
                    last_end,
                    audio_source,
                    url,
                    sessionID,
                    streamID,
                    api,
                    token,
                    raise_interrupt=timeout is None,
                    absolute_timestamps=absolute_timestamps,
                )
        else:
            send_video(audio_source.url, url, sessionID, streamID, api, token)
    except KeyboardInterrupt:
        logger.info("Caught KeyboardInterrupt")

    time.sleep(1)
    send_end(url, sessionID, streamID, api, token)


def read_text(
    url,
    sessionID,
    streamID,
    printing,
    output_file,
    start_time,
    api,
    token,
    titanic_ip,
    generate_video,
    save_video,
):
    send_from = None
    if titanic_ip is not None:
        server_port = (titanic_ip, 8005)
        client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    else:
        client = None

    if not generate_video and save_video is not None:
        header = b"RIFFF\x14h\x01WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00LIST\x1a\x00\x00\x00INFOISFT\x0e\x00\x00\x00Lavf58.29.100\x00data\x00\x14h\x01"  # wav header
        with open(save_video, "wb") as f:
            f.write(header)

    logger.info("Starting SSEClient")
    messages = SSEClient(url + "/" + api + "/stream?channel=" + sessionID)
    for msg in messages:
        if len(msg.data) == 0:
            break

        try:
            data = json.loads(msg.data)
        except json.decoder.JSONDecodeError:
            logger.warning(
                "json.decoder.JSONDecodeError (this may happend when running tts system but no video generation)",
            )
            continue

        if "controll" in data and data["controll"] == "INFORMATION" and "sender" in data:
            sender = data["sender"]
            if sender in data and "display_language" in data[sender] and data[sender]["display_language"] == "en":
                send_from = sender

        if printing == 0:
            if "controll" in data:
                if data["controll"] == "INFORMATION":
                    s = "%s: PROPERTIES: %s" % (data["sender"], data[data["sender"]])
                    logger.info(s)
                    if output_file is not None:
                        with open(output_file, "a") as f:
                            f.write(s + "\n")
                elif data["controll"] == "START":
                    s = "%s: START" % data["sender"]
                    logger.info(s)
                    if output_file is not None:
                        with open(output_file, "a") as f:
                            f.write(s + "\n")
                elif data["controll"] == "END":
                    s = "%s: END" % data["sender"]
                    logger.info(s)
                    if output_file is not None:
                        with open(output_file, "a") as f:
                            f.write(s + "\n")
            else:
                if client is not None and data["sender"] == send_from and "unstable" in data and not data["unstable"]:
                    alex = True
                    start = int(1000 * float(data["start"]))
                    end = int(1000 * float(data["end"]))
                    final = True
                    data_ = (
                        ("0" if alex else "1")
                        + ":"
                        + str(start)
                        + ":"
                        + str(end)
                        + ":"
                        + str(final)
                        + ":"
                        + (data["seq"].replace("<br><br>", ""))
                    )
                    res = str.encode(f"[Request]{data_}")

                    client.sendto(res, server_port)

                if "seq" in data:
                    s = "%s: OUTPUT %.2f-%.2f: %s" % (
                        data["sender"],
                        float(data["start"]),
                        float(data["end"]),
                        data["seq"],
                    )
                    logger.info(s)
                elif data.get("linkedData"):
                    for k, v in data.items():
                        if type(v) is str and v.startswith("/ltapi"):
                            if save_video is not None:
                                logger.info("Downloading", v, "...")
                                res = requests.get(url + v)
                                if res.status_code == 200:
                                    with open(save_video, "ab") as f:
                                        f.write(base64.b64decode(res.json()))
                                    logger.info("Downloading finished.")
                                else:
                                    logger.error("Error during download!")
                            else:
                                logger.info("Received video or audio:", v)
                            break
                    s = None
                if output_file is not None:
                    with open(output_file, "a") as f:
                        f.write(s + "\n")
        elif printing == 1:
            logger.info(data)
            if output_file is not None:
                with open(output_file, "a") as f:
                    f.write(str(data) + "\n")
        elif printing == 2:
            end_time = time.monotonic()
            received_time = end_time - start_time
            logger.info(f"{received_time:.2f}▁{json.dumps(data)}")
            if output_file is not None:
                with open(output_file, "a") as f:
                    f.write(f"{received_time:.2f}▁{json.dumps(data)}\n")


def set_graph(args):
    # More flexible code
    """print("Requesting new session id")
    res = requests.post(args.url + "/"+args.api+"/startsession", cookies={'_forward_auth': args.token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in creating new session")
        sys.exit(1)
    sessionID = res.text
    print("ID:",sessionID)

    print("Adding new stream")
    res = requests.post(args.url + "/"+args.api+"/" + sessionID + "/addstream", cookies={'_forward_auth': args.token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in adding stream to session")
        sys.exit(1)
    streamID = res.text
    print("Stream:",streamID)

    mt = args.run_mt

    print("Setting graph")
    g = {}
    g["user:"+streamID] = ["log", "asr:0"]
    g["asr:0"] = ["log", "api"]
    if mt:
        g["asr:0"].append("mt:0")
        g["mt:0"] = ["log", "api"]
    res = requests.post(args.url + "/"+args.api+"/" + sessionID + "/setgraph", json=json.dumps(g), cookies={'_forward_auth': args.token});
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in setting graph")
        sys.exit(1)"""

    d = {"language": args.asr_properties["language"]} if "language" in args.asr_properties else {}
    if args.run_mt:
        d["mt"] = json.dumps(args.run_mt.split(",") if args.run_mt != "ALL" else "ALL")
    if args.use_prep:
        d["prep"] = True
    if args.upload_video:
        d["log"] = "True"
    else:
        d["log"] = "False" if args.no_logging else "True"
    if args.no_textsegmenter:
        d["textseg"] = False
    d["error_correction"] = args.use_error_correction
    if args.run_tts:
        d["tts"] = args.run_tts
    if args.generate_video:
        d["video"] = args.generate_video

    if args.use_summarize:
        d["summarize"] = True
    if args.use_postproduction:
        d["postproduction"] = True
    if args.speaker_diarization:
        d["speaker_diarization"] = True

    d["asr_prop"] = {k: v for k, v in args.asr_properties.items() if k != "language"}
    d["mt_prop"] = args.mt_properties
    d["prep_prop"] = args.prep_properties
    d["textseg_prop"] = args.textseg_properties
    d["tts_prop"] = args.tts_properties
    d["lip_prop"] = args.video_properties

    logger.info("Requesting default graph for ASR")
    res = requests.post(
        args.url + "/" + args.api + "/get_default_asr",
        json=json.dumps(d),
        cookies={"_forward_auth": args.token},
    )
    if res.status_code != 200:
        if res.status_code == 401:
            logger.info(
                "You are not authorized. Either authenticate with --url https://$username:$password@$server or with --token $token where you get the token from "
                + args.url
                + "/gettoken",
            )
        else:
            logger.error(res.status_code, res.text)
            logger.error("ERROR in requesting default graph for ASR")
        sys.exit(1)
    sessionID, streamID = res.text.split()

    logger.info("SessionId", sessionID, "StreamID", streamID)

    graph = json.loads(
        requests.post(
            args.url + "/" + args.api + "/" + sessionID + "/getgraph",
            cookies={"_forward_auth": args.token},
        ).text,
    )
    logger.info("Graph:", graph)

    return sessionID, streamID


def run_session(args, audio_source):
    sessionID, streamID = set_graph(args)

    start_time = time.monotonic()

    t = Thread(
        target=read_text,
        args=(
            args.url,
            sessionID,
            streamID,
            args.print,
            args.output_file,
            start_time,
            args.api,
            args.token,
            args.titanic_ip,
            args.generate_video,
            args.save_video,
        ),
    )
    t.daemon = True
    t.start()

    time.sleep(1)  # To make sure the SSEClient is running before sending the INFORMATION request

    logger.info("Requesting worker informations")
    data = {"controll": "INFORMATION"}
    info = requests.post(
        args.url + "/" + args.api + "/" + sessionID + "/" + streamID + "/append",
        json=json.dumps(data),
        cookies={"_forward_auth": args.token},
    )
    if info.status_code != 200:
        logger.error(info.status_code, info.text)
        logger.error("ERROR in requesting worker information")
        sys.exit(1)

    send_session(
        args.url,
        sessionID,
        streamID,
        audio_source,
        args.show_on_website,
        args.upload_video,
        args.translate_link,
        args.save_path,
        args.website_title,
        args.meta,
        args.access,
        args.timeout,
        args.api,
        args.token,
        args.absolute_timestamps,
        args.memory_words,
    )

    t.join()


@return_json
@check_status_code
def get_available_languages(args: argparse.Namespace) -> requests.Request:
    """Fetches available languages from the provided API."""
    return requests.post(url=f"{args.url}/{args.api}/list_available_languages", cookies={"_forward_auth": args.token})


@return_json
@check_status_code
def get_active_sessions(args: argparse.Namespace) -> requests.Request:
    url = f"{args.url}/{args.api}/get_active_sessions"
    return requests.get(url=url, cookies={"_forward_auth": args.token})


def print_active_sessions(args: argparse.Namespace) -> None:
    active_sessions: list[str] = get_active_sessions(args)
    if len(active_sessions) == 0:
        logger.info("No active_sessions found")
    for session_string in active_sessions:
        session_entry: dict[str, str] = json.loads(session_string)
        if "session" in session_entry and "host" in session_entry:
            logger.info("Session: %s, Host: %s", session_entry["session"], session_entry["host"])
        else:
            logger.info(json.dumps(session_entry, indent=2))


def main(args):
    if args.list_available_languages:
        logger.info("Listing available languages of mediator")
        logger.info(get_available_languages(args))
        return
    if args.list_active_sessions:
        logger.info("Listing active sessions of mediator")
        print_active_sessions(args)
        return
    if args.upload_video:
        if args.input != "ffmpeg":
            logger.info("To upload a video you have to use ffmpeg input.")
            return
        if args.ffmpeg_input is None:
            logger.info("To upload a video you have to specify the video via ffmpeg_input")
            return
        if args.save_path == "" and args.generate_video is None and args.run_tts is None:
            logger.info(
                "You have to specify the save-path (e.g. /logs/archive/lecture_name/semester/lecture_number), press c to ignore this.",
            )
            breakpoint()
        if "version" not in args.asr_properties or args.asr_properties["version"] != "offline":
            logger.info("To upload a video you have to use offline mode: --asr-kv version=offline")
            return

    audio_source = get_audio_input(args)

    run_session(args, audio_source)


def main_prewait(args, seconds=0):
    time.sleep(seconds)
    main(args)


def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--url", default="https://lt2srv-backup.iar.kit.edu", help="Where to send the audio to")

    parser.add_argument("--token", help="Webapi access token for authentication", default=None)

    parser.add_argument(
        "-i",
        "--input",
        help="Which input type should be used",
        choices=["portaudio", "ffmpeg", "link"],
        default="portaudio",
    )

    parser.add_argument(
        "--print",
        help="specify amount of printing, 0: only hypos, 1: all recieved data, "
        "2: all received data along with received timestamp (s), where start session timestamp = 0",
        type=int,
        default=0,
    )
    parser.add_argument("--list-available-languages", help="List available languages of mediator", action="store_true")
    parser.add_argument("--list-active-sessions", help="List active session on mediator", action="store_true")
    parser.add_argument(
        "--output-file",
        help="Path to the file to save the output translations",
        type=str,
        default=None,
    )

    """
    PyAudio/Portaudio
    """
    parser.add_argument("-L", "--list", help="Pyaudio. List audio available audio devices", action="store_true")
    parser.add_argument("-a", "--audiodevice", help="Pyaudio. Index of audio device to use", default=-1, type=int)

    parser.add_argument(
        "-ch",
        "--audiochannel",
        help="index of audio channel to use (first channel = 1)",
        type=int,
        default=None,
    )

    """
    Ffmpeg
    """
    parser.add_argument("-f", "--ffmpeg-input", help="Input file/address that will be given to ffmpeg", type=str)
    parser.add_argument(
        "--ffmpeg-pre",
        help="ffmpeg options inserted before input parameter (-f)."
        "Don't forget to escape via string so this will be one single parameter."
        "The parameter will be delimited at whitespace and does not support escaping",
        type=str,
    )
    parser.add_argument(
        "--ffmpeg-post",
        help="ffmpeg options inserted after input parameter (-f)."
        "Don't forget to escape via string so this will be one single parameter."
        "The parameter will be delimited at whitespace and does not support escaping",
        type=str,
    )
    parser.add_argument("--volume", help="Adjust the volume via ffmpeg", type=float, default=1.0)
    parser.add_argument(
        "--ffmpeg-speed",
        help="set ffmpeg sending speed, -1 is infinite speed",
        type=float,
        default=1.0,
    )

    parser.add_argument("--upload-video", help="Wether to upload the full ffmpeg input video", action="store_true")
    parser.add_argument("--translate_link", help="Wether to translate a link", action="store_true")
    parser.add_argument("--save-path", help="Where to store the session in the archiv", type=str, default="")

    """ Properties """
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
        help="Used asr properties, e.g. --asr-kv version=online --asr-kv segmenter=VAD --asr-kv stability_detection=False for online or --asr-kv version=offline --asr-kv segmenter=None for offline",
    )
    # If the asr_server runs on a server not reachable from without our network, run e.g.
    # ssh -N -L 0.0.0.0:8001:i13hpc72:5052 i13hpc1.ira.uka.de
    # and use as asr_server
    # --asr-kv asr_server=http://YOUR_CURRENT_IP_ADDRESS:8001/asr/infer/None,None
    parser.add_argument("--no-textsegmenter", help="Set this to not use a textsegmenter", action="store_true")
    parser.add_argument("--textseg-kv", action="append", type=lambda kv: kv.split("="), dest="textseg_properties")

    parser.add_argument("--use-error-correction", action="store_true")

    parser.add_argument(
        "--mt-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="mt_properties",
        help="Used mt properties, e.g. --mt-kv mode=SendStable --mt-kv mt_server=http://URL:PORT/SOMETHING",
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
        help="Used tts properties",
    )
    parser.add_argument(
        "--video-kv",
        action="append",
        type=lambda kv: kv.split("="),
        dest="video_properties",
        help="Used video properties",
    )

    parser.add_argument("--show-on-website", help="Wether to show this session on the website", action="store_true")
    parser.add_argument("--website-title", help="Which title is shown on the website", type=str, default="Audioclient")
    parser.add_argument("--meta", help="Meta information for website title", type=str, default="")
    parser.add_argument("--access", help="Access information for website title", type=str, default="")

    parser.add_argument("--run-scheduler", help="Wether to run scheduler", action="store_true")
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
        help="File to save the generated video locally on this pc to",
        default=None,
        type=str,
    )

    parser.add_argument("--summarize", help="Adds a summarizer after text segmentation.", action="store_true")
    parser.add_argument("--speaker-diarization", help="TODO", action="store_true")

    parser.add_argument("--absolute-timestamps", help="Returns absolute timestamps", action="store_true")

    parser.add_argument("--memory-words", help="Words used in the memory-enhanced ASR model", nargs="+", default=None)

    args = parser.parse_args()

    args.asr_properties = dict(args.asr_properties) if args.asr_properties is not None else {}
    args.mt_properties = dict(args.mt_properties) if args.mt_properties is not None else {}
    args.prep_properties = dict(args.prep_properties) if args.prep_properties is not None else {}
    args.textseg_properties = dict(args.textseg_properties) if args.textseg_properties is not None else {}
    args.tts_properties = dict(args.tts_properties) if args.tts_properties is not None else {}
    args.video_properties = dict(args.video_properties) if args.video_properties is not None else {}
    args.api = "ltapi"
    if args.token is not None:
        args.api = "webapi"

    return args


if __name__ == "__main__":
    arguments = parse()

    if not arguments.run_scheduler:
        logger.info(json.dumps(vars(arguments), indent=4))
        main(arguments)
    else:
        arguments.input = "ffmpeg"
        arguments.asr_properties.update({"mode": "SendUnstable", "language": "en,de"})
        arguments.mt_properties.update({"mode": "SendUnstable"})
        arguments.run_mt = "en-fr,en-it,en-nl,en-es,en-pt"
        arguments.show_on_website = True

        logger.info(json.dumps(vars(arguments), indent=4))

        streams = {
            line.strip().split("\t")[1]: line.strip().split("\t")[4] for line in open("rtmp_list.txt")
        }  # id: rtmp_stream
        sessions = [line.strip().split() for line in open("sessions.txt") if line[0] != "D"]
        logger.info(sessions)

        threads = []
        for timestamp, minutes, room, title in sessions:
            start_time = datetime.strptime(timestamp, "%d.%m.%Y-%H:%M")
            wait_seconds = (start_time - datetime.now()).total_seconds()
            if wait_seconds < 0:
                continue

            args_ = copy.deepcopy(arguments)
            args_.ffmpeg_input = streams[room]
            args_.website_title = title
            args_.timeout = 60 * float(minutes)

            t = Thread(target=main_prewait, args=(args_, wait_seconds))
            t.daemon = True
            threads.append(t)

        logger.info(str(len(threads)) + " sessions are now scheduled.")

        for t in threads:
            t.start()

        for t in threads:
            t.join()
