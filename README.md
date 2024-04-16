# Dialogue Praktikum SS24



## Requirements

### Installing Miniconda3

First, we need to install miniconda. You can download the installer from [here](https://docs.anaconda.com/free/miniconda/index.html). Then run the installer and follow the instructions.

### Creating environment

Using the butler.yaml, we now create a environment with the necessary dependencies such as ffmpeg, python, etc.,

```
conda env create --name butler --file=butler.yml
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
