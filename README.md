<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)

> ## Octopus
> an open-source code interpreter for terminal users

<p align="center">
<img width="1000px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/bc6ed982-9d5c-473d-8efe-dbe6961b200d" align="center"/>

## Getting Started

Prerequisites

* python 3 >= 3.10
* pip
* docker (optional for Docker installation)

Firstly. Install Octopus with the octopus_up script, which will guide you through the setup process, including choosing the Model API service, installation directory, and kernel workspace directory.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://up.dbpunk.xyz | sh
```

To install Octopus with Docker, you must have Docker installed on your local machine. Octopus uses Docker Compose to manage the kernel and agent. The octopus_up script will initialize the Octopus CLI with the generated API key from the agent.

```
octopus_up docker-local
```

To install Octopus without Docker, the kernel and agent will be installed directly to your host. This option is less secure and should only be used for testing or development.

```
octopus_up local
```

## How to use

Open your terminal and execute the command `octopus`, you will see the following output

```text
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```


## How It works

![octopus_simple](https://github.com/dbpunk-labs/octopus/assets/8623385/e5bfb3fb-74a5-4c60-8842-a81ee54fcb9d)

* Octopus Kernel: The code execution engine, based on notebook kernels.
* Octopus Agent: Manages client requests, uses ReAct to process complex tasks, and stores user-assembled applications.
* Octopus Terminal Cli: Accepts user requests, sends them to the Agent, and renders rich results. Currently supports Discord, iTerm2, and Kitty terminals.

For security, it is recommended to run the kernel and agent as Docker containers.

## Features

* Automatically execute AI-generated code in a Docker environment.
* Experiment feature, render images in iTerm2 and kitty.
* Upload files with the /up command and you can use the `/up` in your prompt
* Experiment feature, assemble code blocks into an application and you can run the code directly by `/run` command
* Supports copying output to the clipboard with `/cc` command
* Supports prompt histories stored in the octopus cli

## Roadmap

## Demo

[video](https://github.com/dbpunk-labs/octopus/assets/8623385/bea76119-a705-4ae1-907d-cb4e0a0c18a5)


### API Service Supported

|name|status| note|
|----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) | ✅ fully supported|the detail installation steps|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |  ✅ fully supported|the detail install steps|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) | ✔️  supported| You must start the llama cpp server by yourself|


### Platforms Supported

|name|status| note|
|----|----------------|---|
|ubuntu 22.04 | ✅ fully supported|the detail installation steps|
|macos |  ✅ fully supported|the detail install steps|

### Deployment

## Home Labs Solutions

## Medias
python & bash: requirements.txt
typescripts: tslab , tslab install

## Thanks

* [Octopus icons created by Whitevector - Flaticon](https://www.flaticon.com/free-icons/octopus)
