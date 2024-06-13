import os

from pydub import AudioSegment


directory_path = "C:\\Users\\namid\\PycharmProjects\\NLP_practical\\tests\\test_data_temp"
for filename in os.listdir(directory_path):
    file_path = os.path.join(directory_path, filename)
    if os.path.isfile(file_path):
        sound = AudioSegment.from_file(file_path)
        two_sec_silence = AudioSegment.silent(duration=2000)

        new_sound = sound + two_sec_silence
        new_sound.export(file_path, format="mp3")


# sound = AudioSegment.from_file("C:\\Users\\namid\\PycharmProjects\\NLP_practical\\tests\\test_data\\get_next_appointment13.mp3")
#
# two_sec_silence = AudioSegment.silent(duration=3000)
#
#
# new_sound = sound + two_sec_silence #+ noise
# new_sound.export("C:\\Users\\namid\\PycharmProjects\\NLP_practical\\tests\\test_data\\get_next_appointment13.mp3", format="mp3")
