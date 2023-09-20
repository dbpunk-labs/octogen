<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)

Octopus is an open-source code interpreter for terminal users

<p align="center">
<img width="800px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/5609a3d7-b82e-494f-817f-37ff88544320" align="center"/>


## Getting Started

## How It works

Core components

* Kernel: The code execution engine, based on notebook kernels.
* Agent: Manages client requests, uses ReAct to process complex tasks, and stores user-assembled applications.
* Chat: Accepts user requests, sends them to the Agent, and renders rich results. Currently supports Discord, iTerm2, and Kitty terminals.

For security, it is recommended to run the kernel and agent as Docker containers.


## Demo

[video](https://github.com/dbpunk-labs/octopus/assets/8623385/1b7a47e5-8ac9-4d42-9eb2-848b47b8db84)

### API Service Supported

|name|status| note|
|----|----------------|---|
|Openai GPT 3.5/4 | ✅ fully supported|the detail installation steps|
|Azure Openai GPT 3.5/4 |  ✅ fully supported|the detail install steps|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) | ✅ fully supported| You must provide the model|

### Deployment

## Home Labs Solutions

## Medias
python & bash: requirements.txt
typescripts: tslab , tslab install

## Thanks

* [Octopus icons created by Whitevector - Flaticon](https://www.flaticon.com/free-icons/octopus)
