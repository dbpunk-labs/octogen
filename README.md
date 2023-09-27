<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)
[![PyPI - Version](https://img.shields.io/pypi/v/octopus_chat)](https://pypi.org/project/octopus-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/octopus_chat?logo=pypi)

[中文](./README_zh_cn.md)

> ## Octogen
> an open-source code interpreter for developers

<p align="center">
<img width="1000px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/3ccb2d00-7231-4014-9dc5-f7f3e487c8a2" align="center"/>

|OS|Platform|
|----|----------------|
|![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)| ✅ |
|![macOS](https://img.shields.io/badge/mac%20os-000000?style=for-the-badge&logo=macos&logoColor=F0F0F0)|✅ |
|![ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white) |✅|

## Getting Started

Requirement
* python 3.10 and above
* pip
* docker 24.0.0 and above

> To deploy Octopus, the user needs permission to run Docker commands.   
> To use codellama, your host must have at least 8 CPUs and 16 GB of RAM.

Install the octopus on your local computer

1. Install og_up

```bash
pip install og_up
```
> try to change the pip mirror if the step install octopus terminal cli takes a lot of time

2. Set up the Octopus service
   
```
og_up
```

> You can choose the openai, azure openai, codellama and octopus agent sevice
> Ocotopus will download codellama from huggingface.co if you choose codellama
> If the installation of the Octopus Terminal CLI takes a long time, consider changing the pip mirror.

3. Open your terminal and execute the command `og`, you will see the following output

```
Welcome to use octogen❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```

## Supported API Service

|name|type|status| installation|
|----|-----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) |LLM| ✅ fully supported|use `octopus_up` then choose the `OpenAI`|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |LLM|  ✅ fully supported|use `octopus_up` then choose the `Azure OpenAI`|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) |LLM| ✔️  supported | use `octopus_up` then choose the `CodeLlama` |
|[Octopus Agent Service](https://dbpunk.xyz) |Code Interpreter| ✅ supported | use `octopus_up` then choose the `Octopus` |


## The internal of Octopus

![octopus_simple](https://github.com/dbpunk-labs/octopus/assets/8623385/e5bfb3fb-74a5-4c60-8842-a81ee54fcb9d)

* Octopus Kernel: The code execution engine, based on notebook kernels.
* Octopus Agent: Manages client requests, uses ReAct to process complex tasks, and stores user-assembled applications.
* Octopus Terminal Cli: Accepts user requests, sends them to the Agent, and renders rich results. Currently supports Discord, iTerm2, and Kitty terminals.

## Demo

[video](https://github.com/dbpunk-labs/octopus/assets/8623385/bea76119-a705-4ae1-907d-cb4e0a0c18a5)

## Features

* Automatically execute AI-generated code in a Docker environment.
* Experiment feature, render images in iTerm2 and kitty.
* Upload files with the `/up` command and you can use it in your prompt
* Experiment feature, assemble code blocks into an application and you can run the code directly by `/run` command
* Support copying output to the clipboard with `/cc` command
* Support prompt histories stored in the octopus cli

if you have any feature suggestion. please create a discuession to talk about it

## Roadmap

* [roadmap for v0.5.0](https://github.com/dbpunk-labs/octopus/issues/64)


