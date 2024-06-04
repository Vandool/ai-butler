from __future__ import annotations

import logging
import queue
import sys
import threading

import numpy as np
import pyaudio
import watchdog

from src.pythonrecordingclient.helper import BugException
from src.pythonrecordingclient.inputStreamAdapter import BaseAdapter


def read_audio(stream, chunk_size, queue):
    while True:
        chunk = stream.read(chunk_size, exception_on_overflow=False)
        queue.put(chunk)


class PortaudioStream(BaseAdapter):
    def __init__(self, chunk_size: int = 1024) -> None:
        self.chunk_size = chunk_size
        self.input_id: int | None = None
        self._stream: pyaudio.Stream | None = None
        self._pyaudio: pyaudio.PyAudio | None = None
        self.queue = queue.Queue()
        self.read_thread: threading.Thread | None = None
        self.running = False
        super().__init__(format=pyaudio.paInt16)

    def get_stream(self) -> pyaudio.Stream:
        if self.input_id is None:
            raise BugException
        if self._stream is None:
            p = self.pyaudio
            self._stream = p.open(
                format=self.format,
                input_device_index=self.input_id,
                channels=self.channel_count,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            thread = threading.Thread(target=read_audio, args=(self._stream, self.chunk_size, self.queue))
            thread.daemon = True
            thread.start()
        return self._stream

    def read(self) -> bytes:
        self.get_stream()

        size = max(self.queue.qsize(), 1)
        chunks = [self.queue.get() for _ in range(size)]

        if len(chunks) > 75:
            print("WARNING: Network is to slow. Having at least 5 seconds of delay!")

        return b"".join(chunks)

    def chunk_modify(self, chunk: bytes) -> bytes:
        if self.chosen_channel is not None and self.channel_count > 1:
            # filter out specific channel using numpy
            logging.info("Using numpy to filter out specific channel.")
            data = np.fromstring(chunk, dtype="int16").reshape((-1, self.channel_count))
            data = data[:, self.chosen_channel - 1]
            if watchdog:
                watchdog.sent_audio(data)
            chunk = data.tostring()
        return chunk

    def cleanup(self) -> None:
        self.stop()
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        if self._pyaudio is not None:
            self._pyaudio.terminate()
            self._pyaudio = None

    def set_input(self, id: int) -> None:
        devices = self.get_audio_devices()
        try:
            devName = devices[id]
            self.input_id = id
        except (ValueError, KeyError):
            self.print_all_devices()
            sys.exit(1)

    def get_audio_devices(self) -> dict[int, str]:
        devices = {}

        p = self.pyaudio
        info = p.get_host_api_info_by_index(0)
        deviceCount = info.get("deviceCount")

        for i in range(deviceCount):
            if p.get_device_info_by_host_api_device_index(0, i).get("maxInputChannels") > 0:
                devices[i] = p.get_device_info_by_host_api_device_index(0, i).get("name")
        return devices

    def print_all_devices(self) -> None:
        """
        Special command, prints all audio devices available
        """
        print("-- AUDIO devices:")
        devices = self.get_audio_devices()
        for key in devices:
            dev = devices[key]
            if isinstance(dev, bytes):
                dev = dev.decode("ascii", "replace")
            print("    id=%i - %s" % (key, dev))

    @property
    def pyaudio(self) -> pyaudio.PyAudio:
        if self._pyaudio is None:
            self._pyaudio = pyaudio.PyAudio()
        return self._pyaudio

    def set_audio_channel_filter(self, channel: int) -> None:
        # actually chosing a specific channel is apparently impossible with portaudio,
        # so we record all channels instead and then filter out the wanted channel with numpy
        if self.input_id is None:
            raise BugException()
        channelCount = self.pyaudio.get_device_info_by_host_api_device_index(0, self.input_id).get("maxInputChannels")
        self.channel_count = channelCount
        self.chosen_channel = channel

    def start(self) -> None:
        """Start the audio stream."""
        self.running = True
        self.get_stream()
        if self.read_thread is None:
            self.read_thread = threading.Thread(target=self._read_audio)
            self.read_thread.daemon = True
            self.read_thread.start()

    def stop(self) -> None:
        """Stop the audio stream."""
        self.running = False
        if self.read_thread is not None:
            self.read_thread.join()
            self.read_thread = None

    def _read_audio(self) -> None:
        while self.running:
            chunk = self._stream.read(self.chunk_size, exception_on_overflow=False)
            self.queue.put(chunk)
