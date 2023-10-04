<p align="center">
<img  width="200px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/86af130f-7d0d-4cfb-9410-fc338426938e" align="center"/>


![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octogen/ci.yaml)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)
[![PyPI - Version](https://img.shields.io/pypi/v/og_chat)](https://pypi.org/project/og-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/og_chat?logo=pypi)

[中文](./README_zh_cn.md)

> ## Octogen
> an open-source code interpreter for developers

<p align="center">
<img src="https://github.com/imotai/test_repos/blob/main/gifs/octogen_demo.gif?raw=true" align="center"/>


|Supported OS|
|----|
|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/31b907e9-3a6f-4e9e-b0c0-f01d1e758a21"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/565d5f93-baac-4a77-ab1c-7d845e2fdb6d"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/acb7f919-ef09-446e-b1bc-0b50bc28de5a"/>|



## Getting Started

Requirement
* python 3.10 and above
* pip
* [docker](https://www.docker.com/products/docker-desktop/) 24.0.0 and above, docker desktop is recommended

> To deploy Octogen, the user needs permission to run Docker commands.   
> To use codellama, your host must have at least 8 CPUs and 16 GB of RAM.

Install the octogen on your local computer

1. Install og_up

```bash
pip install og_up
```
> try to change the pip mirror if the step install octopus terminal cli takes a lot of time

2. Set up the Octogen service
   
```
og_up
```

> You have the option to select from OpenAI, Azure OpenAI, CodeLlama, and Octogen agent services.
> If you opt for CodeLlama, Octogen will automatically download it from huggingface.co.
> In case the installation of the Octogen Terminal CLI is taking longer than expected, you might want to consider switching to a different pip mirror.

3. Open your terminal and execute the command `og`, you will see the following output

```
Welcome to use octogen❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```
## Development


Prepare the environment

```
git clone https://github.com/dbpunk-labs/octogen.git
cd octogen
python3 -m venv octogen_venv
source octogen_venv/bin/activate
pip install -r requirements.txt
```

Run the sandbox including Agent with mock model and Kernel

```
$ bash start_sandbox.sh
$ og

Welcome to use octogen❤️ . To ask a programming question, simply type your question and press esc + 
enter
Use /help for help

[1]🎧>hello
╭─ 🐙Octogen ─────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                     │
│  0 🧠 how can I help you today?                                                                     │
│                                                                                                     │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
[2]🎧>

```

* To use openai for development, just update the config in the `start_sandbox.sh` with the example of [openai-env.example](./env_sample/openai_env.sample)
* To use azure openai for development, just update the config in the `start_sandbox.sh` with the example of [azure-env.example](./env_sample/azure_env.sample)
* To use codellama for development, just update the config in the `start_sandbox.sh` with the example of [codellama-env.example](./env_sample/codellama_env.sample)

## Supported API Service


|name|type|status| installation|
|----|-----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) |LLM| ✅ fully supported|use `og_up` then choose the `OpenAI`|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |LLM|  ✅ fully supported|use `og_up` then choose the `Azure OpenAI`|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) |LLM| ✔️  supported | use `og_up` then choose the `CodeLlama` |
|[Octopus Agent Service](https://octogen.dev) |Code Interpreter| ✅ supported | apply api key from [octogen.dev](https://www.octogen.dev/) then use `og_up` then choose the `Octogen` |


## The internal of local deployment

![octogen-internal drawio](https://github.com/dbpunk-labs/octogen/assets/8623385/95dd6f84-6de8-476a-9c66-9ab591ed9b0e)

* Octogen Kernel: The code execution engine, based on notebook kernels.
* Octogen Agent: Manages client requests, uses ReAct to process complex tasks, and stores user-assembled applications.
* Octogen Terminal Cli: Accepts user requests, sends them to the Agent, and renders rich results. Currently supports Discord, iTerm2, and Kitty terminals.

## Features

* Automatically execute AI-generated code in a Docker environment.
* Experiment feature, render images in iTerm2 and kitty.
* Upload files with the `/up` command and you can use it in your prompt
* Experiment feature, assemble code blocks into an application and you can run the code directly by `/run` command
* Support copying output to the clipboard with `/cc` command
* Support prompt histories stored in the octopus cli

if you have any feature suggestion. please create a discuession to talk about it

## Roadmap

* [roadmap for v0.5.0](https://github.com/dbpunk-labs/octogen/issues/64)


