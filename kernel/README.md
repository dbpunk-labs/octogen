# The Kernel Server for Python Execution

## Run the Kernel Server

```shell
pip install .
```

## Request the Kernel Server

```shell
python3 -m websockets ws://127.0.0.1:9527
>  {"method":"start", "params":[], "id":0}
< {"result": "ready", "id": 0}
> {"method":"stop", "params":[], "id":1}
< {"result": "stop", "id": 1}
```
