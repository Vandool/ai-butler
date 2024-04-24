#!/usr/bin/env python3

import subprocess as sp
from builtins import str
from datetime import datetime, timedelta
from time import mktime


class BugException(Exception):
    def __init__(self, msg="You have found a bug. Please contact a developer with the command and all output.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


def extract_pcm_audio(video_file: str, out_file: str) -> None:
    cmd = [
        "ffmpeg", "-y", "-i", video_file, "-vn", "-c:a", "pcm_s16le",
        "-ac", "1", "-ar", "16000", out_file,
    ]
    p = sp.Popen(cmd)
    p.communicate()


def escape(text):
    text = text.replace("ö", "oe")
    text = text.replace("Ö", "Oe")
    text = text.replace("ä", "ae")
    text = text.replace("Ä", "Ae")
    text = text.replace("ü", "ue")
    text = text.replace("Ü", "Ue")
    text = text.replace("ß", "ss")
    return text


def objToXml(oName, obj):
    attributes = {}
    for key in obj:
        if isinstance(obj[key], str):
            attributes[key] = escape(obj[key])
        elif isinstance(obj[key], int):
            attributes[key] = str(obj[key])
    elements = { key: obj[key] for key in obj if isinstance(obj[key], dict)}
    lists = { key: obj[key] for key in obj if isinstance(obj[key], list)}
    res = "<" + oName
    for name, value in attributes.items():
        res += " " + name + '="' + value + '"'
    res += ">"
    for name, value in lists.items():
        for item in value:
            res += objToXml(name, item)
    for name, value in elements.items():
        res += objToXml(name, value)
    res += "</" + oName + ">"
    return res


def toStamp(dt: datetime) -> int:
    return int(mktime(dt.timetuple()) * 1000000) + dt.microsecond


def toDatetime(ts: int) -> datetime:
    ts, ms = divmod(ts, 1000000)
    return datetime.fromtimestamp(ts) + timedelta(microseconds=ms)
