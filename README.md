<p align="center">
<img  width="150px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/86af130f-7d0d-4cfb-9410-fc338426938e" align="center"/>


![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octogen/ci.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/og_chat)](https://pypi.org/project/og-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/og_chat?logo=pypi)
[![Gitter](https://img.shields.io/gitter/room/octogen/%20)](https://matrix.to/#/#octogen:gitter.im)

[中文](./README_zh_cn.md)

> ## Octogen
> an open-source code interpreter   
>  一款开源可本地部署的代码解释器

https://github.com/dbpunk-labs/octogen/assets/8623385/7445cc4d-567e-4d1a-bedc-b5b566329c41


|Supported OSs|Supported Interpreters|Supported Dev Enviroment|
|----|-----|-----|
|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/31b907e9-3a6f-4e9e-b0c0-f01d1e758a21"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/565d5f93-baac-4a77-ab1c-7d845e2fdb6d"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/acb7f919-ef09-446e-b1bc-0b50bc28de5a"/>|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/6e286d3d-55f8-43df-ade6-38065b78eda1"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/958d23a0-777c-4bb9-8480-c7350c128c3f"/>|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/ec8d5bff-f4cf-4870-baf9-3b0c53f39273"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/70602050-6a04-4c63-bb1a-7b35e44a8c79"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/fb543a9b-5235-45d4-b102-d57d21b2e237"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/8c1c5048-6c4a-40c9-b234-c5c5e0d53dc1"/>|



## Getting Started

Requirement
* python 3.10 and above
* pip
* [docker](https://www.docker.com/products/docker-desktop/) 24.0.0 and above, or [podman](https://podman.io/)

> To deploy Octogen, the user needs permission to run Docker commands.   
> To use codellama, your host must have at least 8 CPUs and 16 GB of RAM.

Install the octogen on your local computer

1. Install og_up

```bash
pip install og_up
```

2. Set up the Octogen service
   
```
og_up
```
You have the following options to select 
* OpenAI , recommanded for daily use
* Azure OpenAI
* CodeLlama, 
* Octogen agent services powered by GPT4 and Codellama 34B

The default is using docker as container engine. use podman with flag `--use_podman` 

3. Execute the command `og`, you will see the following output

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


![octogen-internal](https://github.com/dbpunk-labs/octogen/assets/8623385/986f6805-44cf-4bc7-868f-1f6a987ca254)

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


