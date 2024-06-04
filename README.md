# Dialogue Praktikum SS24

## Lecture Timings

Wednesdays, 3:45 p.m. - 5:15 p.m. Seminar Room 223  (We will begin from 24/04/2024)

## Requirements

In the first lecture, we will provide the user ids and password that is necessary to access the hosted services. PLEASE
DO NOT SHARE THEM. If we find the servers to be overloaded, we have to stop serving them.

### Installing Miniconda3

First, we need to install miniconda. You can download the installer
from [here](https://docs.anaconda.com/free/miniconda/index.html). Then run the installer and follow the instructions.

### Creating environment

Using the butler.yaml, we now create a environment with the necessary dependencies such as ffmpeg, python, etc.,

```
conda env create --name butler --file=butler.yml
conda activate butler
```

This should create the environment with required dependencies to connect with the ASR and MT system hosted in the
lecture translator.

##### Sanity Check #1

To make sure everything is working properly, we will run the client.py script to list our audio devices. Run the
following in your command line

```
python client.py -L
```

This should list all the available microphone devices in your computer. Later, you can note the id for the microphone
you want to use and pass it as a parameter.

### Querying LLM

At our Lab cluster, we provide a hosted [Llama2 13B Chat](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf) that
students can access. For this, you need to install the following library

```
pip install huggingface-hub
```

Then, I will provide you with a URL that you can send requests to. For example, you can prompt the LLM as follows

##### Sanity Check #2

```
from huggingface_hub import InferenceClient

client = InferenceClient(model="http://127.0.0.1:8080") ## Replace with address you recieve for the LLM
client.text_generation(prompt="Write a code for snake game")
```

For further information on how to generate with different decoding strategies, prompt formatting etc, refer to the
documentation [here](https://huggingface.co/docs/text-generation-inference/en/basic_tutorials/consuming_tgi)

## Authentication

First, you need to login with KIT account by going here [Login Page](https://lt2srv-backup.iar.kit.edu/login)
Once you login, then access your token by going here [Get Token](https://lt2srv-backup.iar.kit.edu/gettoken)

You can use the token to test the starter code next.

## Starter Code - Fun Fact Generator

If everything is installed properly, then you can test the sample code that we provide. Every message that is recieved
will be sent to the process function in butler.py

We did a simple implementation to detect if the user has said fun by keyword spotting and then generates a fun fact
about germany. Try the demo_client.py with the following command

```
python demo_client.py -a {Your microphone id that you want to use} -u {The URL with id and password that we will provide} -llm {The LLM address for the hosted LLama2}
python demo_client.py -a 1 --token Cn1mh=|wfwf|sai.koneru@kit.edu --llm https://awesomellama.com 
```

This should print the ASR transcript and give you a fun fact when ever you say fun.

# WHAT AN AWESOME PROJECT NAME

## Overview

This project is part of a course and contains both provided materials from the lecturer and our own code.

## Project Structure

The folder `src` contains the source code that we develop. To ensure package independence and maintain organization, we
copy the code that we require into the `src` in an appropriate package.

```bash
dialogue_praktikum/
├── <<provided_code>>/     # Code and materials provided by the lecturer
├── reports /          # Test reports
├── src/               # Our custom-developed code
├── tests/             # Test suites
│   ├── e2e/           # End-to-end tests
│   └── unit-tests/    # Unit tests
├── README.md
└── ...
```

## New Dependencies

Our code relies on several external libraries. The primary dependencies we have added are:

- `sentence-transformers`: A library for state-of-the-art sentence embeddings.
- `pytorch`: The PyTorch deep learning framework, which is required by `sentence-transformers`.
- `fuzzywuzzy`: A library for fuzzy string matching.
- `python-Levenshtein`: A library for fast computation of Levenshtein distance.
-

### Installing Dependencies

To install the dependencies, you can use the provided `requirements.txt` file. Here’s how you can set up your
environment:

1. **Update your already working conda environment**:
   ```sh
   conda activate butler
   pip install transformers -U
   pip install sentence-transformers
   
   # for speedy fuzzy word detection
   pip install fuzzywuzzy
   pip install python-Levenshtein

# Google Calendar API Integration

This guide provides step-by-step instructions to set up and use the Google Calendar API with a service account. Follow
these steps to create a Google Cloud account, set up credentials, and configure the environment for API usage.

## Table of Contents

1. [Google Cloud Setup](#google-cloud-setup)
2. [Calendar Sharing](#calendar-sharing)
3. [Retrieving Calendar ID](#retrieving-calendar-id)
4. [Environment Variables](#environment-variables)

## Google Cloud Setup

1. **Create Google Cloud Account**:
    - Go to [Google Cloud Console](https://console.cloud.google.com/) and sign in or create a new account.

2. **Create a New Project**:
    - Navigate to the project selector and click "New Project".
    - Enter your project name and click "Create".

3. **Enable APIs**:
    - Go to the "API & Services" > "Library".
    - Search for "Google Calendar API" and click "Enable".

4. **Create Service Account Credentials**:
    - Go to "API & Services" > "Credentials".
    - Click "Create Credentials" and select "Service Account".
    - Fill in the service account details and click "Done".
    - Navigate to the service account you just created, click on it, and go to the "Keys" tab.
    - Click "Add Key" > "Create New Key" and select JSON. Save the JSON file.

## Calendar Sharing

1. **Share the Calendar**:
    - Go to [Google Calendar](https://calendar.google.com) and sign in with your Google account.
    - On the left sidebar under "My calendars," find the calendar you want to share.
    - Click on the three dots next to the calendar name and select "Settings and sharing".
    - Scroll down to the "Share with specific people" section.
    - Click "Add people" and enter the service account email (found in the JSON file under the `client_email` field).
    - Set the permissions to "Make changes to events".
    - Click "Send" to share the calendar.

## Retrieving Calendar ID

To retrieve your Google Calendar ID:

1. **Open Google Calendar**:
    - Go to [Google Calendar](https://calendar.google.com) and sign in with your Google account.

2. **Access Calendar Settings**:
    - On the left sidebar under "My calendars," find the calendar you want to use.
    - Click on the three dots next to the calendar name and select "Settings and sharing".

3. **Find Calendar ID**:
    - Scroll down to the "Integrate calendar" section.
    - The "Calendar ID" will be listed there. It usually looks like `your-email@gmail.com`
      or `your-calendar-id@group.calendar.google.com`.

## Environment Variables

Create a `.env` file in your project root directory and add the following environment variables:

```ini
GC_PRIVATE_KEY = YOUR_PRIVATE_KEY
GC_CLIENT_EMAIL = YOUR_CLIENT_EMAIL
GC_PROJECT_ID = YOUR_PROJECT_ID
GC_PRIVATE_KEY_ID = YOUR_PRIVATE_KEY_ID
GC_CLIENT_ID = YOUR_CLIENT_ID
GC_CALENDAR_ID = YOUR_CALENDAR_ID
```

Replace the placeholders with values extracted from the service account JSON file and the Google Calendar ID.

*When running the application make sure you have specified the location of the `.env` to the runner.*


### Text2Speech

1. Install the following packages:
   ```sh
   pip install simpleaudio
   pip install soundfile
   pip install pydub
