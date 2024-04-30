
import argparse
import base64
import json
import queue
import secrets
import string
import sys
import time
from threading import Thread

import requests
from sseclient import SSEClient

from pythonrecordingclient.helper import BugException
from webhandler import webutils
from webhandler.ltweb import LTHandler
from webhandler.zoomweb import ZoomHandler

cities = ["Hong Kong","Bangkok","London","Macau","Singapore","Paris","Dubai","New York City","Kuala Lumpur","Istanbul","Delhi","Tokyo","Seoul","Barcelone","Amsterdam","Milan","Taipei","Rome","Osaka","Vienna","Shanghai","Pargue","Los Angeles","Madird","Munich"]


driver = webutils.create_driver()
driver.get("https://witeboard.com/")

zoom_handler = ZoomHandler(driver=driver)
lt_handler = LTHandler(driver=driver)

cmd_queue = queue.Queue()



def run_command(data):
    '''
    This function is called when command is recieved with markup and handles routing selenium 
    Input Example: {'seq': '{"function":"controll_zoom","parameter":{"command":"join","link":"https://kit-lecture.zoom-x.de/j/61573381905?pwd=YkE3aUNYSnhXSnJnREMrV2VSMy85Zz09"}}', 'markup': 'command', 'session': '1182', 'sender': 'kitmeetingbutler:0', 'message_id': 2, 'num_subscribers': '1'}
    Returns: Executes the command independently
    '''
    if "controll_zoom" in data["seq"]: ## Start Join or End video calls
        zoom_handler.handle_command(data["seq"])
        return

    if "controll_lt" in data["seq"]: ## Start Join or End Lecture Translator
        lt_handler.handle_command(data["seq"])
        return

    if "set_display" in data["seq"]:
        command = json.loads(data["seq"])
        if command["parameter"]["page"] == "video_conference":
            if zoom_handler.handle != None:
                zoom_handler.driver.switch_to.window(zoom_handler.handle)
        if command["parameter"]["page"] == "lecture_translator":
            if lt_handler.handle != None:
                lt_handler.driver.switch_to.window(lt_handler.handle )
        if command["parameter"]["page"] == "whiteboard":
            driver.switch_to.window(driver.window_handles[0])
        if command["parameter"]["page"] == "controll":
            driver.switch_to.window(driver.window_handles[1])

def cmd_worker(cmd_queue):
    while True:
        cmd_data = cmd_queue.get()
        if cmd_data is not None:
            run_command(cmd_data)
            cmd_queue.task_done()

cmd_thread = Thread(target=cmd_worker, args=(cmd_queue,))
cmd_thread.start()


def verify_chunk_size(value: str | int) -> int:
    try:
        val: int = int(value)
        assert(val > 0)
    except:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
    return val

def get_audio_input(args):
    if args.input == "link":
        return args.ffmpeg_input
    if args.input == "portaudio":
        from pythonrecordingclient.pyaudioStreamAdapter import PortaudioStream

        print("Using portaudio as input. If you want to use ffmpeg specify '-i ffmpeg'.")
        stream_adapter = PortaudioStream()
        input = args.audiodevice
        if args.list:
            stream_adapter.print_all_devices()
        if args.audiodevice < 0:
            print("The portaudio backend requires the '-a' parameter. Run python client.py -L to see the available audio devices.")
            exit(1)
    else:
        raise BugException()

    stream_adapter.set_input(input)

    return stream_adapter

def send_start(url, sessionID, streamID, api, token):


    print("Start sending audio")

    data={"controll":"START"}
    data["type"] = "meeting_room"
    data["name"] = secrets.choice(cities)
    print("Name:",data["name"])
    alphabet = string.ascii_uppercase + string.digits
    #data["password"] = ''.join(secrets.choice(alphabet) for i in range(5))
    data["password"] = "AI4LT"
    print("Name:",data["name"]," ",data["password"])
    info = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})



    if info.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in starting session")
        sys.exit(1)

    global driver

    driver.execute_script("""window.open("https://lt2srv-backup.iar.kit.edu/overview/meeting_room","_blank");""")
    driver.switch_to.window(driver.window_handles[-1])

    driver = webutils.click_id_button("start" + str(sessionID),driver)
    driver = webutils.enter_text("password", data["password"], driver, enter=True)


def send_keepalive(url, sessionID, streamID, api, token):
    print("Send keep alive")
    data= {"markup":"command"}
    command = {"function": "keep_alive","parameter":{}}
    data["seq"] = json.dumps(command)
    info = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})
    if info.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in starting session")
        sys.exit(1)


def send_audio(audio_source, url, sessionID, streamID, api, token, raise_interrupt=True):
    chunk = audio_source.read()
    chunk = audio_source.chunk_modify(chunk)
    s = time.time()
    e = s + len(chunk)/32000
    data = {"b64_enc_pcm_s16le":base64.b64encode(chunk).decode("ascii"),"start":s,"end":e}
    res = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in sending audio")
        sys.exit(1)
    #else:
        #print(len(chunk))

def send_video(videopath, url, sessionID, streamID, api, token):
    video = open(videopath,"rb").read()
    data = {"b64_enc_audio":base64.b64encode(video).decode("ascii")}
    res = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in sending video")
        sys.exit(1)
    print("Video successfully sent.")

def send_link(videopath, url, sessionID, streamID, api, token):
    data = {"url":videopath}
    res = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in sending video")

        sys.exit(1)
    print("Video successfully sent.")


def send_end(url, sessionID, streamID, api, token):
    print("Sending END.")
    data={"controll": "END"}
    res = requests.post(url + "/"+api+"/" + sessionID + "/" + streamID + "/append", json=json.dumps(data), cookies={"_forward_auth": token})
    if res.status_code != 200:
        print(res.status_code,res.text)
        print("ERROR in sending END message")
        sys.exit(1)


def send_session(url, sessionID, voice_stream_ID,text_stream_ID,command_ID, audio_source, api, token):
    try:
        start_time = time.time()
        send_start(url, sessionID, voice_stream_ID, api, token)

        while(True):
            time.sleep(30)
            send_keepalive(url,sessionID,command_ID,api,token)

        last_end = 0
        while (True):
            send_audio( audio_source, url, sessionID, voice_stream_ID, api, token)

    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt")

    time.sleep(1)
    send_end(url, sessionID, voice_stream_ID, api, token)

def read_text(url, sessionID, api,token):

    send_from = None
    client = None




    print("Starting SSEClient")
    messages = SSEClient(url + "/"+api+"/stream?channel=" + sessionID)
    for msg in messages:
        if len(msg.data) == 0:
            break

        try:
            data = json.loads(msg.data)
            print(data)
            if "markup" in data and data["markup"] == "command":

                cmd_queue.put(data)
                #cmd_thread = Thread(target=run_command, args=(data,))
                #cmd_thread.start()

        except json.decoder.JSONDecodeError:
            print("WARNING: json.decoder.JSONDecodeError (this may happend when running tts system but no video generation)")
            continue

        print(data)

def set_graph(args):

    print("Requesting default graph for ASR")
    d={}
    d["bot"] = "kitmeetingbutler"
    res = requests.post(args.url + "/"+args.api+"/start_dialog", json=json.dumps(d), cookies={"_forward_auth": args.token})
    if res.status_code != 200:
        if res.status_code == 401:
            print("You are not authorized. Either authenticate with --url https://$username:$password@$server or with --token $token where you get the token from "+args.url+"/gettoken")
        else:
            print(res.status_code,res.text)
            print("ERROR in requesting default graph for ASR")
        sys.exit(1)
    sessionID, voice_stream_ID,text_stream_ID,command_ID = res.text.split()

    print("SessionId",sessionID,"StreamID",voice_stream_ID," ",text_stream_ID," ",command_ID)

    print("Setting properties")
    graph=json.loads(requests.post(args.url+"/"+args.api+"/"+sessionID+"/getgraph", cookies={"_forward_auth": args.token}).text)
    print("Graph:",graph)

    return sessionID, voice_stream_ID,text_stream_ID,command_ID

def run_session(args, audio_source):

    sessionID, voice_stream_ID,text_stream_ID,command_ID = set_graph(args)


    start_time = time.monotonic()

    t = Thread(target=read_text,
               args=(args.url, sessionID, args.api, args.token))
    t.daemon = True
    t.start()

    time.sleep(1) # To make sure the SSEClient is running before sending the INFORMATION request

    print("Requesting worker informations")
    data={"controll":"INFORMATION"}
    info = requests.post(args.url + "/"+args.api+"/" + sessionID + "/" + voice_stream_ID + "/append", json=json.dumps(data), cookies={"_forward_auth": args.token})
    if info.status_code != 200:
        print(info.status_code,info.text)
        print("ERROR in requesting worker information")
        sys.exit(1)

    send_session(args.url, sessionID, voice_stream_ID,text_stream_ID,command_ID, audio_source, args.api, args.token)
    t.join()

def get_available_languages(args):
    info = requests.post(args.url + "/"+args.api+"/list_available_languages", cookies={"_forward_auth": args.token})
    if info.status_code != 200:
        print(info.status_code,info.text)
        print("ERROR in listing languages")
        sys.exit(1)
    return info.json()

def print_active_sessions():
    info = requests.get(args.url + "/"+args.api+"/get_active_sessions", cookies={"_forward_auth": args.token})
    if info.status_code != 200:
        print(info.status_code,info.text)
        print("ERROR in listing active sessions")
        sys.exit(1)
    sessions = info.json()
    if len(sessions) == 0:
        print("No sessions found")
    for s in sessions:
        s = json.loads(s)
        if "session" in s and "host" in s:
            print("Session:",s["session"],"Host:",s["host"])
        else:
            print(s)

def main(args):

    audio_source = get_audio_input(args)
    run_session(args, audio_source)

def main_prewait(args, seconds=0):
    time.sleep(seconds)
    main(args)

def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument("-u",
                        "--url",
                        default="https://lt2srv-backup.iar.kit.edu",
                        help="Where to send the audio to")

    parser.add_argument("--token", help="Webapi access token for authentication", default=None)

    parser.add_argument("-i", "--input", help="Which input type should be used", choices=["portaudio", "ffmpeg","link"], default="portaudio")


    """
    PyAudio/Portaudio
    """
    parser.add_argument("-L", "--list", help="Pyaudio. List audio available audio devices", action="store_true")
    parser.add_argument("-a", "--audiodevice", help="Pyaudio. Index of audio device to use", default=-1, type=int)

    parser.add_argument("-ch", "--audiochannel", help="index of audio channel to use (first channel = 1)", type=int, default=None)


    """ Properties """

    args = parser.parse_args()

    args.api = "ltapi"

    return args

if __name__ == "__main__":
    args = parse()

    print("args",args)
    main(args)

