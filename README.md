<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)
[![PyPI - Version](https://img.shields.io/pypi/v/octopus_chat)](https://pypi.org/project/octopus-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/octopus_chat?logo=pypi)

[中文](./README_zh_cn.md)

> ## Octopus
> an open-source code interpreter for developers

<p align="center">
<img width="1000px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/3ccb2d00-7231-4014-9dc5-f7f3e487c8a2" align="center"/>

|OS|Platform|
|----|----------------|
|windows10 | ✅ x86|
|macOS |✅ x86, ✅ m2|
|ubuntu |✅ x86|

## Getting Started

Requirement
* python 3.10 and above
* pip
* docker 24.0.0 and above

> To deploy Octopus, the user needs permission to run Docker commands.
> To use codellama, your host must have at least 8 CPUs and 16 GB of RAM.

Install the octopus on your local computer

1. Install octopus_up

```bash
pip install octopus_up
```

2. Set up the Octopus service using the OpenAI API key or the Codellama.

```
octopus_up
```
> You can choose the openai, azure openai and codellama
> Ocotopus will download codellama from huggingface.co if you choose codellama

3. Open your terminal and execute the command `octopus`, you will see the following output

```
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```

## Supported API Service

|name|status| installation|
|----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) | ✅ fully supported|the detail installation steps|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |  ✅ fully supported|the detail install steps|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) | ✔️  supported | You must have match the minimal hardware requirement |


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
* Upload files with the /up command and you can use the `/up` in your prompt
* Experiment feature, assemble code blocks into an application and you can run the code directly by `/run` command
* Support copying output to the clipboard with `/cc` command
* Support prompt histories stored in the octopus cli

if you have any feature suggestion. please create a discuession to talk about it

## Plan

* Improve the stability of octopus and security
* Support external codellama api service
* Support memory system
* Enhence the agent programming capability
* Enhence the kernel capability
    * support gpu to accelerate processing of video

if you have any advice for the roadmap. please create a discuession to talk about it


## VPS Deployment

|name|location| recommanded hardware|
|----|----------------|---|
|kernel|Your own VPS|todo|
|Agent|Your own VPS|todo|
|Model|GPT3.5|todo|


## Home Labs Deployment

Recommanded hardware configuration

|name|configuration| installation|
|----|--------------|---|
|CPU|8c|todo|
|Memory|32G|todo|
|GPU|3090|todo|
|Model|Codellama 13B|todo|

## UI Supported

|name|status| installation|
|----|----------------|---|
|terminal | ✅ fully supported|the detail installation steps|
|desktop | on the plan| You must start the llama cpp server by yourself|

## Platforms Supported

|name|status| installation|
|----|----------------|---|
|ubuntu 22.04 | ✅ fully supported|the detail installation steps|
|macos |  ✅ fully supported|the detail install steps|

