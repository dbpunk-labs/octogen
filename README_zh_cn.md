<p align="center">
<img width="100px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/6c60cb2b-415f-4979-9dc2-b8ce1958e17a" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octopus/ci.yml?branch=main&style=flat-square)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/UjSHsjaz66)
[![Twitter Follow](https://img.shields.io/twitter/follow/OCopilot7817?style=flat-square)](https://twitter.com/OCopilot7817)
[![PyPI - Version](https://img.shields.io/pypi/v/octopus_chat)](https://pypi.org/project/octopus-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dd/octopus_chat)

[English](./README.md)
> ## Octopus
> 一款为终端用户打造地开源的代码解释器

<p align="center">
<img width="1000px" src="https://github.com/dbpunk-labs/octopus/assets/8623385/3ccb2d00-7231-4014-9dc5-f7f3e487c8a2" align="center"/>

## 快速上手

在本地电脑安装octopus, 你可以选择使用openai 或者codellama-7B

本地环境要求
* python 3 >= 3.10
* pip
* docker

安装octopus启动器

```bash
pip install octopus_up
```

使用octopus启动器初始化本地环境,这一步你需要选择使用openai或者codellama-7B

```
octopus_up
```

开始体验octopus, 在命令行执行`octopus`

```
Welcome to use octopus❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```

## Octopus内部实现

![octopus_simple](https://github.com/dbpunk-labs/octopus/assets/8623385/e5bfb3fb-74a5-4c60-8842-a81ee54fcb9d)

* Octopus 内核: 当前基于notebook实现的代码执行引擎
* Octopus Agent: 处理用户请求，将请求发给大模型服务API和将大模型生成的代码发给Octopus 内核执行代码
* Octopus 命令行工具: 将用户请求发给Agent和渲染Agent返回的代码，文本和图片

每个组件之间都是采用流式方式进行数据交换，大模型每写一个字都会在命令行上面实时展示.

## 功能列表

* 在docker环境自动执行代码
* 实验功能，在iterm2 和kitty终端进行图片显示
* 支持通过`/up`命令将文件上传到Octopus内核，你可以在写问题描述的过程中使用上床文件命令
* 实验功能， 支持将大模型生成的代码片段打包在一起生成一个应用，然后通过`/run` 命令直接执行
* 支持将输出内容文本，代码通过 `/cc`命令复制到粘贴板上面
* 支持问题历史功能，提问历史将会被保存在本地

如果你有功能需求建议，可以创建一个讨论帖子和大家一起讨论

## 后续计划 

* 提升octopus的可用性和安全性
* 支持记忆系统，让octopus能过更好服务每个人
* 增强agent的代码生成能力
* 增强kernel的代码执行能力
    * 支持gpu加速视频处理领域任务

当前整个计划都处于草稿状态，如果你愿意参与讨论，欢迎加入dicord讨论组交流
## Demo

[video](https://github.com/dbpunk-labs/octopus/assets/8623385/bea76119-a705-4ae1-907d-cb4e0a0c18a5)


## API服务支持列表

|名字|状态| 安装步骤|
|----|----------------|---|
|[Openai GPT 3.5/4](https://openai.com/product#made-for-developers) | ✅ 完整支持|使用OpenAI接口安装步骤|
|[Azure Openai GPT 3.5/4](https://azure.microsoft.com/en-us/products/ai-services/openai-service) |  ✅ 完整支持|使用微软OpenAI接口安装步骤|
|[LLama.cpp Server](https://github.com/ggerganov/llama.cpp/tree/master/examples/server) | ✔️  部分支持| 使用llama.cpp server安装步骤|

## 支持平台列表

|名字|状态|安装不受|
|----|----------------|---|
|ubuntu 22.04 | ✅ fully supported|详细安装步骤|
|macos |  ✅ fully supported|详细安装步骤|
|windows |  ✅ fully supported|详细安装步骤|

