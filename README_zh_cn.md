<p align="center">
<img  width="200px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/86af130f-7d0d-4cfb-9410-fc338426938e" align="center"/>

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/dbpunk-labs/octogen/ci.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/og_chat)](https://pypi.org/project/og-chat/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/og_chat?logo=pypi)
[![Gitter](https://img.shields.io/gitter/room/octogen/%20)](https://app.gitter.im/#/room/#octogen:gitter.im)

[English](./README.md)
> ## Octopus
> 一款为开发者打造的开源的代码解释器

<p align="center">

<video src="https://github.com/dbpunk-labs/octogen/assets/8623385/7445cc4d-567e-4d1a-bedc-b5b566329c41" controls="controls" style="max-width: 730px;">
</video>

|Supported OSs|Supported Interpreters|Supported Dev Enviroment|
|----|-----|-----|
|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/31b907e9-3a6f-4e9e-b0c0-f01d1e758a21"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/565d5f93-baac-4a77-ab1c-7d845e2fdb6d"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/acb7f919-ef09-446e-b1bc-0b50bc28de5a"/>|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/6e286d3d-55f8-43df-ade6-38065b78eda1"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/958d23a0-777c-4bb9-8480-c7350c128c3f"/>|<img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/ec8d5bff-f4cf-4870-baf9-3b0c53f39273"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/70602050-6a04-4c63-bb1a-7b35e44a8c79"/><img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/fb543a9b-5235-45d4-b102-d57d21b2e237"/> <img  width="40px" src="https://github.com/dbpunk-labs/octogen/assets/8623385/8c1c5048-6c4a-40c9-b234-c5c5e0d53dc1"/>|



## 快速上手

在本地电脑安装octopus, 你可以选择使用openai 或者codellama-7B

本地环境要求
* python 3.10 and above
* pip
* [docker](https://www.docker.com/products/docker-desktop/) 24.0.0 and above or [Podman](https://podman.io/)


安装octogen启动器

```bash
pip install og_up
```

使用og_up启动器初始化本地环境
```
og_up
```

开始体验octogen, 在命令行执行`og`

```
Welcome to use octogen❤️ . To ask a programming question, simply type your question and press esc + enter
You can use /help to look for help

[1]🎧>
```

## Octopus内部实现

![octogen-internal drawio](https://github.com/dbpunk-labs/octogen/assets/8623385/95dd6f84-6de8-476a-9c66-9ab591ed9b0e)

* Octopus 内核: 当前基于notebook实现的代码执行引擎
* Octopus Agent: 处理用户请求，将请求发给大模型服务API和将大模型生成的代码发给Octopus 内核执行代码
* Octopus 命令行工具: 将用户请求发给Agent和渲染Agent返回的代码，文本和图片

每个组件之间都是采用流式方式进行数据交换，大模型每写一个字都会在命令行上面实时展示.

## 功能列表

* 在docker环境自动执行代码
* 实验功能，在iterm2 和kitty终端进行图片显示
* 支持通过`/up`命令将文件上传到Octopus内核，你可以在写问题描述的过程中使用上传文件命令
* 实验功能， 支持将大模型生成的代码片段打包在一起生成一个应用，然后通过`/run` 命令直接执行
* 支持将输出内容文本和代码通过 `/cc`命令复制到粘贴板上面
* 支持问题历史功能，提问历史将会被保存在本地

如果你有功能需求建议，可以创建一个讨论帖子和大家一起讨论

## 计划

* [roadmap for v0.5.0](https://github.com/dbpunk-labs/octogen/issues/64)

