from __future__ import annotations

import abc
from pathlib import Path

import numpy as np
import simpleaudio as sa
import soundfile as sf
import torch
from datasets import load_dataset
from pydub import AudioSegment
from transformers import pipeline


class TextToSpeech(abc.ABC):
    @abc.abstractmethod
    def text_to_speech(self, text: str, *args, **kwargs) -> None:
        pass


class MicrosoftSpeechT5TTS(TextToSpeech):
    def __init__(
        self,
        model_name="microsoft/speecht5_tts",
        embedding_dataset="Matthijs/cmu-arctic-xvectors",
        model_path: Path | None = None,
    ):
        if model_path and self.__model_exists(model_path):
            self.synthesiser = self.__load_model(model_path)
        else:
            self.synthesiser = pipeline("text-to-speech", model=model_name)
            self.__save_model(self.synthesiser, model_path)

        self.embeddings_dataset = load_dataset(embedding_dataset, split="validation")

    def text_to_speech(self, text: str, speaker_embedding_index: int = 7306, **kwargs):  # noqa: ARG002
        return self.play_audio(
            speech=self.synthesize_speech(text=text, speaker_embedding_index=speaker_embedding_index),
        )

    def synthesize_speech(self, text: str, speaker_embedding_index: int = 7306):
        return self.synthesiser(
            text,
            forward_params={
                "speaker_embeddings": (self.__get_speaker_embedding(speaker_embedding_index)),
            },
        )

    @staticmethod
    def play_audio(speech) -> None:
        audio_data = np.array(speech["audio"])
        audio_data = (audio_data * 32767).astype(np.int16)  # Convert to 16-bit PCM format
        audio_segment = AudioSegment(
            audio_data.tobytes(),
            frame_rate=speech["sampling_rate"],
            sample_width=2,
            channels=1,
        )
        play_obj = sa.play_buffer(
            audio_segment.raw_data,
            num_channels=audio_segment.channels,
            bytes_per_sample=audio_segment.sample_width,
            sample_rate=audio_segment.frame_rate,
        )
        play_obj.wait_done()  # Wait for playback to finish

    def __get_speaker_embedding(self, index):
        return torch.tensor(self.embeddings_dataset[index]["xvector"]).unsqueeze(0)

    @staticmethod
    def save_audio(speech, file_name: Path) -> None:
        sf.write(file_name, speech["audio"], samplerate=speech["sampling_rate"])

    @staticmethod
    def __save_model(model, path: Path) -> None:
        if path:
            torch.save(model, path)

    @staticmethod
    def __load_model(path: Path):
        return torch.load(path)

    @staticmethod
    def __model_exists(path: Path) -> bool:
        return path and Path.exists(path)


# Example usage
if __name__ == "__main__":
    tts = MicrosoftSpeechT5TTS(model_path=Path.cwd() / "models" / "speecht5_tts.pt")
    for text_ in [
        "Hello, my dog is cooler than you!",
        "You should meet your mom at her house at seventeen o'clock (roughly in three hours). You're going to plan a party with her.",
    ]:
        speech = tts.synthesize_speech(text_)
        # Play the audio
        tts.play_audio(speech)
