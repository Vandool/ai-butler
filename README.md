# Dialogue Praktikum SS24

## Lecture Timings

Wednesdays, 3:45 p.m. - 5:15 p.m. Seminar Room 223  (We will begin from 24/04/2024)

## Requirements

In the first lecture, we will provide the user ids and password that is necessary to access the hosted services. PLEASE DO NOT SHARE THEM. If we find the servers to be overloaded, we have to stop serving them.

### Installing Miniconda3

First, we need to install miniconda. You can download the installer from [here](https://docs.anaconda.com/free/miniconda/index.html). Then run the installer and follow the instructions.

### Creating environment

Using the butler.yaml, we now create a environment with the necessary dependencies such as ffmpeg, python, etc.,

```
conda env create --name butler --file=butler.yml
conda activate butler
```

This should create the environment with required dependencies to connect with the ASR and MT system hosted in the lecture translator.

##### Sanity Check #1

To make sure everything is working properly, we will run the client.py script to list our audio devices. Run the following in your command line

```
python client.py -L
```
This should list all the available microphone devices in your computer. Later, you can note the id for the microphone you want to use and pass it as a parameter.

### Querying LLM

At our Lab cluster, we provide a hosted [Llama2 13B Chat](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf) that students can access. For this, you need to install the following library

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

For further information on how to generate with different decoding strategies, prompt formatting etc, refer to the documentation [here](https://huggingface.co/docs/text-generation-inference/en/basic_tutorials/consuming_tgi)

## Starter Code - Fun Fact Generator

If everything is installed properly, then you can test the sample code that we provide. Every message that is recieved will be sent to the process function in butler.py 

We did a simple implementation to detect if the user has said fun by keyword spotting and then generates a fun fact about germany. Try the demo_client.py with the following command

```
python demo_client.py -a {Your microphone id that you want to use} -u {The URL with id and password that we will provide} -llm {The LLM address for the hosted LLama2}
python demo_client.py -a 1 -u http://skoneru:mypwd@ltserver.iar.kit.edu --llm https://awesomellama.com 
```

This should print the ASR transcript and give you a fun fact when ever you say fun.
