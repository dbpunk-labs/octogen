<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)
[![PyPI - Version](https://img.shields.io/pypi/v/octopus_chat)](https://pypi.org/project/octopus-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/octopus_chat)

[中文](./README_zh_cn.md)

> ## Octopus
> an open-source code interpreter for developers

<p align="center">
<img width="1000px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/3ccb2d00-7231-4014-9dc5-f7f3e487c8a2" align="center"/>


## Getting Started

Install the octopus with codellama-7B in your local computer

Prerequisites

* python 3 >= 3.10
* pip
* docker, the current use must be in the docker group

1. Install octopus_up

```bash
pip install octopus_up
```

2. Set up the Octopus service using the OpenAI API key or the embedding model Codellama-7b.

```
octopus_up
```

3. Open your terminal and execute the command `octopus`, you will see the following output

```
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```


## The internal of Octopus

![octopus_simple](https://github.com/dbpunk-labs/octopus/assets/8623385/e5bfb3fb-74a5-4c60-8842-a81ee54fcb9d)

* Octopus Kernel: The code execution engine, based on notebook kernels.
* Octopus Agent: Manages client requests, uses ReAct to process complex tasks, and stores user-assembled applications.
* Octopus Terminal Cli: Accepts user requests, sends them to the Agent, and renders rich results. Currently supports Discord, iTerm2, and Kitty terminals.


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

## Demo

[video](https://github.com/dbpunk-labs/octopus/assets/8623385/bea76119-a705-4ae1-907d-cb4e0a0c18a5)


## UI Supported

|name|status| installation|
|----|----------------|---|
|terminal | ✅ fully supported|the detail installation steps|
|webui | on the plan|the detail install steps|
|desktop | on the plan| You must start the llama cpp server by yourself|

## API Service Supported

|name|status| installation|
|----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) | ✅ fully supported|the detail installation steps|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |  ✅ fully supported|the detail install steps|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) | ✔️  supported| You must start the llama cpp server by yourself|

## Platforms Supported

|name|status| installation|
|----|----------------|---|
|ubuntu 22.04 | ✅ fully supported|the detail installation steps|
|macos |  ✅ fully supported|the detail install steps|

