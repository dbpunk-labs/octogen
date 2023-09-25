#! /bin/sh
#
# start_all.sh
# Copyright (C) 2023 ubuntu <ubuntu@ip-172-31-29-132>
#
# Distributed under terms of the MIT license.
#

if [ "$#" -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

ROOT_DIR=$1
echo "start kernel.."
cd ${ROOT_DIR}/kernel && hap run -n octopus_kernel -- octopus_kernel_rpc_server

echo "start agent"
cd ${ROOT_DIR}/agent && hap run -n octopus_agent -- octopus_agent_rpc_server

if [ "$2" -eq 1 ]
then
echo "start codellama"
mkdir -p ${ROOT_DIR}/model_server
cd ${ROOT_DIR}/model_server && hap run -n codellama -- server -t 4  -m ../model/codellama-7b-instruct.Q4_K_M.gguf  --alias codellama-7b --host 127.0.0.1 --port 8080
fi

sleep 3

AGENT_RPC_KEY=$(cat ${ROOT_DIR}/agent/.env | grep admin_key | cut -d "=" -f 2)
KERNEL_RPC_KEY=$(cat ${ROOT_DIR}/kernel/.env | grep rpc_key | cut -d "=" -f 2)
octopus_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}

while true
do
    hap status
    sleep 5
done

