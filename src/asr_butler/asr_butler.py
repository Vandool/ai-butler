from __future__ import annotations

import argparse
import base64
import copy
import datetime
import json
import os
import socket
import sys
import time
from pathlib import Path
from threading import Thread

import requests
from huggingface_hub import InferenceClient
from sseclient import SSEClient

from src import utils
from src.config.asr_llm_config import get_asr_llm_config
from src.history.history import History
from src.llm_client.llm_client import LLMClient
from src.pythonrecordingclient.ffmpegStreamAdapter import FfmpegStream
from src.pythonrecordingclient.helper import BugException
from src.pythonrecordingclient.pyaudioStreamAdapter import PortaudioStream
from src.state.state import InitialState, State
from src.text2speech.microsoft_speecht5_tts import MicrosoftSpeechT5TTS, TextToSpeech
from src.web_handler.my_web_utils import check_status_code, return_json

logger = utils.get_logger("ASRModule")


class ASRModule:
    def __init__(  # noqa: PLR0913
        self,
        args: argparse.Namespace,
        history: History | None,
        llm_client: LLMClient | None,
        start_state: State | None = None,
        tts_client: TextToSpeech | None = None,
    ):
        self.history = history
        self.llm_client = llm_client
        self.state = start_state
        self.text_to_speech = tts_client
        self.args = args
        self.api = args.api
        self.token = args.token
        self.url = args.url
        self.session_id = None
        self.stream_id = None
        self.transcript_buffer = ""
        if self.args.output_file:
            output_path = Path(self.args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.labeled_info_pretty(label="Available Languages", info=self.get_available_languages())
        logger.labeled_info_pretty(label="Active Sessions", info=self.get_active_sessions())
        if args.audio_device < 0:
            self.list_and_select_audio_device()
        self.audio_source = self.set_audio_input()

    def list_and_select_audio_device(self):
        stream_adapter = PortaudioStream()
        available_devices = stream_adapter.get_audio_devices()

        stream_adapter.print_all_devices()
        while True:
            try:
                selected_device = int(input("Please select the audio device number: "))
                if selected_device in available_devices:
                    self.args.audio_device = selected_device
                    logger.info(f"Selected audio device: {available_devices[selected_device]}")
                    break
                logger.warning("Invalid selection. Please enter a valid device number.")
            except ValueError:
                logger.exception("Invalid input. Please enter a number.")

    def set_audio_input(self):
        if self.args.input == "link":
            return self.args.ffmpeg_input
        if self.args.input == "portaudio":
            logger.info("Using portaudio as input_. If you want to use ffmpeg specify '-i ffmpeg'.")
            # (Arvand): Added the chunk_size to control the chunk size while playing around
            stream_adapter = PortaudioStream(chunk_size=self.args.chunk_size)
            input_ = self.args.audio_device
            if self.args.audio_device < 0:
                logger.info(
                    "The portaudio backend requires the '-a' parameter. Run python client.py -L to see the available audio devices.",
                )
                sys.exit(1)
        elif self.args.input == "ffmpeg":
            stream_adapter = FfmpegStream(
                pre_input=self.args.ffmpeg_pre,
                post_input=self.args.ffmpeg_post,
                volume=self.args.volume,
                repeat_input=False,
                ffmpeg_speed=self.args.ffmpeg_speed,
            )
            input_ = self.args.ffmpeg_input
            if input_ is None:
                logger.info("The ffmpeg backend requires an url/file via the '-f' parameter")
                sys.exit(1)
            elif not os.path.isfile(input_) and not input_.startswith("rtsp"):
                logger.info(f"File {input_} does not exist")
                sys.exit(1)
        else:
            raise BugException

        stream_adapter.set_input(input_)
        return stream_adapter

    def send_start(self):
        logger.info("Start sending audio")
        data = {"controll": "START"}
        if self.args.show_on_website:
            data["type"] = "lecture"
            data["name"] = self.args.website_title
        if self.args.meta:
            data["meta"] = self.args.meta
        if self.args.access:
            data["access"] = self.args.access
        if self.args.save_path != "":
            data["directory"] = self.args.save_path
        info = requests.post(
            f"{self.url}/{self.api}/{self.session_id}/{self.stream_id}/append",
            json=json.dumps(data),
            cookies={"_forward_auth": self.token},
        )
        if info.status_code != 200:
            logger.error(info.status_code, info.text)
            logger.error("ERROR in starting session")
            sys.exit(1)

    def send_audio(self, last_end, raise_interrupt=True, absolute_timestamps=False):
        chunk = self.audio_source.read()
        chunk = self.audio_source.chunk_modify(chunk)
        if raise_interrupt and len(chunk) == 0:
            raise KeyboardInterrupt
        s = last_end if not absolute_timestamps else time.time()
        e = s + len(chunk) / 32000
        data = {"b64_enc_pcm_s16le": base64.b64encode(chunk).decode("ascii"), "start": s, "end": e}
        res = requests.post(
            f"{self.url}/{self.api}/{self.session_id}/{self.stream_id}/append",
            json=json.dumps(data),
            cookies={"_forward_auth": self.token},
        )
        if res.status_code != 200:
            logger.error(res.status_code, res.text)
            logger.error("ERROR in sending audio")
            sys.exit(1)
        return e

    def send_end(self):
        logger.info("Sending END.")
        data = {"controll": "END"}
        res = requests.post(
            f"{self.url}/{self.api}/{self.session_id}/{self.stream_id}/append",
            json=json.dumps(data),
            cookies={"_forward_auth": self.token},
        )
        if res.status_code != 200:
            logger.error(res.status_code, res.text)
            logger.error("ERROR in sending END message")
            sys.exit(1)

    @check_status_code
    def send_link(self):
        data = {"url": self.url}
        res = requests.post(
            self.audio_source.url + "/" + self.args.api + "/" + self.session_id + "/" + self.stream_id + "/append",
            json=json.dumps(data),
            cookies={"_forward_auth": self.args.token},
        )
        if res.status_code != 200:
            logger.error(res.status_code, res.text)
            logger.error("ERROR in sending video")
            sys.exit(1)
        logger.info("Video successfully sent.")

    def send_session(self):
        try:
            start_time = time.time()
            self.send_start()
            if self.args.memory_words is not None:
                self.send_memory(self.args.memory_words)
            if self.args.translate_link:
                self.send_link()
            elif not self.args.upload_video:
                last_end = 0
                while self.args.timeout is None or time.time() - start_time < self.args.timeout:
                    last_end = self.send_audio(
                        last_end,
                        raise_interrupt=self.args.timeout is None,
                        absolute_timestamps=self.args.absolute_timestamps,
                    )
            else:
                self.send_video(self.audio_source.url)
        except KeyboardInterrupt:
            logger.info("Caught KeyboardInterrupt")

        time.sleep(1)
        self.send_end()

    def read_text(self, start_time: float) -> None:
        send_from = None
        if self.args.titanic_ip is not None:
            server_port = (self.args.titanic_ip, 8005)
            client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        else:
            client = None

        if not self.args.generate_video and self.args.save_video is not None:
            header = b"RIFFF\x14h\x01WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00LIST\x1a\x00\x00\x00INFOISFT\x0e\x00\x00\x00Lavf58.29.100\x00data\x00\x14h\x01"
            with open(self.args.save_video, "wb") as f:
                f.write(header)

        logger.info("Starting SSEClient")
        messages = SSEClient(f"{self.url}/{self.api}/stream?channel={self.session_id}")
        for msg in messages:
            if len(msg.data) == 0:
                break

            try:
                data = json.loads(msg.data)
            except json.decoder.JSONDecodeError:
                logger.warning(
                    "json.decoder.JSONDecodeError (this may happen when running TTS system but no video generation)",
                )
                continue

            if "controll" in data and data["controll"] == "INFORMATION" and "sender" in data:
                sender = data["sender"]
                if sender in data and "display_language" in data[sender] and data[sender]["display_language"] == "en":
                    send_from = sender

            if self.args.print_level == 0:
                if "controll" in data:
                    self._process_controll_data(data)
                else:
                    if (
                        client is not None
                        and data["sender"] == send_from
                        and "unstable" in data
                        and not data["unstable"]
                    ):
                        alex = True
                        start = int(1000 * float(data["start"]))
                        end = int(1000 * float(data["end"]))
                        final = True
                        data_ = f"0:{start}:{end}:{final}:{data['seq'].replace('<br><br>', '')}"
                        res = str.encode(f"[Request]{data_}")

                        client.sendto(res, server_port)

                    if "seq" in data:
                        self.transcript_buffer += data["seq"]

                        asr_output = "{}: OUTPUT {:.2f}-{:.2f}: {}".format(
                            data["sender"],
                            float(data["start"]),
                            float(data["end"]),
                            data["seq"],
                        )
                        logger.info(asr_output)
                        self._save_str_output(asr_output)

                        if self._is_sentence_complete(data):
                            full_sentence = self.transcript_buffer.strip()
                            self.transcript_buffer = ""
                            logger.info("full sentence: %s", full_sentence)
                            self.process_command(full_sentence)

                    elif data.get("linkedData"):
                        for v in data.values():
                            if isinstance(v, str) and v.startswith("/ltapi"):
                                if self.args.save_video is not None:
                                    logger.info(f"Downloading {v}...")
                                    res = requests.get(f"{self.url}{v}")
                                    if res.status_code == 200:
                                        with open(self.args.save_video, "ab") as f:
                                            f.write(base64.b64decode(res.json()))
                                        logger.info("Downloading finished.")
                                    else:
                                        logger.error("Error during download!")
                                else:
                                    logger.info(f"Received video or audio: {v}")
                                break
            elif self.args.print_level == 1:
                logger.info_pretty(data)
                self._save_json_output(data)
            elif self.args.print_level == 2:
                end_time = time.monotonic()
                received_time = end_time - start_time
                asr_output = {
                    "received_time": received_time,
                    "data": data,
                }
                logger.info_pretty(asr_output)
                self._save_json_output(asr_output)

    def _process_controll_data(self, data: dict) -> None:
        asr_output = (
            {
                "sender": data["sender"],
                "properties": data[data["sender"]],
            }
            if data["controll"] == "INFORMATION"
            else {
                "sender": data["sender"],
                "status": data["controll"],
            }
        )
        logger.info_pretty(asr_output)
        self._save_json_output(asr_output)

    @staticmethod
    def _is_sentence_complete(data: dict) -> bool:
        segment_end_key = "speech_segment_ends"
        return segment_end_key in data and data["speech_segment_ends"]

    def _save_json_output(self, data: dict):
        self._save_str_output(json.dumps(data, indent=2))

    def _save_str_output(self, data: str):
        if self.args.output_file:
            output_path = Path(self.args.output_file)
            with output_path.open("a") as f:
                f.write(data + "\n")

    def process_command(self, user_input: str):
        if self.state:
            self.state = self.state.process(user_input)

    @return_json
    @check_status_code
    def get_available_languages(self) -> requests.Request:
        """Fetches available languages from the provided API."""
        return requests.post(
            url=f"{self.args.url}/{self.args.api}/list_available_languages",
            cookies={"_forward_auth": self.args.token},
        )

    @return_json
    @check_status_code
    def get_active_sessions(self) -> requests.Request:
        url = f"{self.args.url}/{self.args.api}/get_active_sessions"
        return requests.get(url=url, cookies={"_forward_auth": self.args.token})

    def print_active_sessions(self) -> None:
        active_sessions: list[str] = self.get_active_sessions()
        if len(active_sessions) == 0:
            logger.info("No active_sessions found")
        for session_string in active_sessions:
            session_entry: dict[str, str] = json.loads(session_string)
            if "session" in session_entry and "host" in session_entry:
                logger.info("Session: %s, Host: %s", session_entry["session"], session_entry["host"])
            else:
                logger.info(json.dumps(session_entry, indent=2))

    def set_graph(self):
        d = {"language": self.args.asr_properties["language"]} if "language" in self.args.asr_properties else {}
        if self.args.run_mt:
            d["mt"] = json.dumps(self.args.run_mt.split(",") if self.args.run_mt != "ALL" else "ALL")
        if self.args.use_prep:
            d["prep"] = True
        d["log"] = "True" if self.args.upload_video else "False" if self.args.no_logging else "True"
        d["error_correction"] = self.args.use_error_correction
        if self.args.run_tts:
            d["tts"] = self.args.run_tts
        if self.args.generate_video:
            d["video"] = self.args.generate_video
        if self.args.use_summarize:
            d["summarize"] = True
        if self.args.use_postproduction:
            d["postproduction"] = True
        if self.args.speaker_diarization:
            d["speaker_diarization"] = True

        d["asr_prop"] = {k: v for k, v in self.args.asr_properties.items() if k != "language"}
        d["mt_prop"] = self.args.mt_properties
        d["prep_prop"] = self.args.prep_properties
        d["textseg_prop"] = self.args.textseg_properties
        d["tts_prop"] = self.args.tts_properties
        d["lip_prop"] = self.args.video_properties

        logger.info("Requesting default graph for ASR")
        res = requests.post(
            f"{self.args.url}/{self.args.api}/get_default_asr",
            json=json.dumps(d),
            cookies={"_forward_auth": self.args.token},
        )
        if res.status_code != 200:
            if res.status_code == 401:
                logger.info(
                    f"You are not authorized. Either authenticate with --url https://$username:$password@$server or with --token $token where you get the token from {self.args.url}/gettoken",
                )
            else:
                logger.error(res.status_code, res.text)
                logger.error("ERROR in requesting default graph for ASR")
            sys.exit(1)
        self.session_id, self.stream_id = res.text.split()

        logger.info("SessionId %s, StreamID %s", self.session_id, self.stream_id)

    def run_session(self):
        self.set_graph()

        start_time = time.monotonic()

        t = Thread(
            target=self.read_text,
            args=(start_time,),
        )
        t.daemon = True
        t.start()

        time.sleep(1)  # To make sure the SSEClient is running before sending the INFORMATION request

        logger.info("Requesting worker informations")
        data = {"controll": "INFORMATION"}
        info = requests.post(
            f"{self.url}/{self.api}/{self.session_id}/{self.stream_id}/append",
            json=json.dumps(data),
            cookies={"_forward_auth": self.token},
        )
        if info.status_code != 200:
            logger.error(info.status_code, info.text)
            logger.error("ERROR in requesting worker information")
            sys.exit(1)

        self.send_session()

        t.join()

    def run_immediate_session(self):
        if self.args.list_available_languages:
            logger.info("Listing available languages of mediator")
            logger.info(self.get_available_languages())
            return
        if self.args.list_active_sessions:
            logger.info("Listing active sessions of mediator")
            self.print_active_sessions()
            return
        if self.args.upload_video:
            if self.args.input != "ffmpeg":
                logger.info("To upload a video you have to use ffmpeg input.")
                return
            if self.args.ffmpeg_input is None:
                logger.info("To upload a video you have to specify the video via ffmpeg_input")
                return
            if self.args.save_path == "" and self.args.generate_video is None and self.args.run_tts is None:
                logger.info(
                    "You have to specify the save-path (e.g. /logs/archive/lecture_name/semester/lecture_number), press c to ignore this.",
                )
                breakpoint()
            if "version" not in self.args.asr_properties or self.args.asr_properties["version"] != "offline":
                logger.info("To upload a video you have to use offline mode: --asr-kv version=offline")
                return

        self.run_session()

    def schedule_sessions(self):
        self.args.input = "ffmpeg"
        self.args.asr_properties.update({"mode": "SendUnstable", "language": "en,de"})
        self.args.mt_properties.update({"mode": "SendUnstable"})
        self.args.run_mt = "en-fr,en-it,en-nl,en-es,en-pt"
        self.args.show_on_website = True

        logger.info(json.dumps(vars(self.args), indent=4))

        streams = {
            line.strip().split("\t")[1]: line.strip().split("\t")[4] for line in open("rtmp_list.txt")
        }  # id: rtmp_stream
        sessions = [line.strip().split() for line in open("sessions.txt") if line[0] != "D"]
        logger.info(sessions)

        threads = []
        for timestamp, minutes, room, title in sessions:
            start_time = datetime.datetime.strptime(timestamp, "%d.%m.%Y-%H:%M")
            wait_seconds = (start_time - datetime.datetime.now()).total_seconds()
            if wait_seconds < 0:
                continue

            args_ = copy.deepcopy(self.args)
            args_.ffmpeg_input = streams[room]
            args_.website_title = title
            args_.timeout = 60 * float(minutes)

            t = Thread(target=self.main_prewait, args=(args_, wait_seconds))
            t.daemon = True
            threads.append(t)

        logger.info(f"{len(threads)!s} sessions are now scheduled.")

        for t in threads:
            t.start()

        for t in threads:
            t.join()

    def main_prewait(self, seconds=0):
        time.sleep(seconds)
        self.run_immediate_session()

    def run_asr_module(self):
        if not self.args.run_scheduler:
            logger.info(json.dumps(vars(self.args), indent=4))
            self.run_immediate_session()
        else:
            self.schedule_sessions()


class TheButler(ASRModule):
    """ASRModule is the butler, the butler is ASR"""


if __name__ == "__main__":
    arguments = get_asr_llm_config()
    llm_client_ = LLMClient(client=InferenceClient(arguments.llm_url))
    tts = MicrosoftSpeechT5TTS(model_path=Path.cwd() / "models" / "speecht5_tts.pt")
    asr_module = TheButler(
        args=arguments,
        history=History(),
        llm_client=llm_client_,
        start_state=InitialState(llm_client=llm_client_, tts_client=tts),
        tts_client=tts,
    )
    asr_module.run_session()
