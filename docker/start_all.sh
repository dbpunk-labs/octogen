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

if [ "$2" -eq 1 ]
then
    if [ -z "$3" ]
    then
        echo "no model name" 
        exit 1
    else
        echo "start codellama with model name $3"
        mkdir -p ${ROOT_DIR}/model_server
        cd ${ROOT_DIR}/model_server && hap run -n codellama -- server -m ../model/$3  --alias codellama --host 127.0.0.1 --port 8080
    fi
fi

echo "start kernel.."
cd ${ROOT_DIR}/kernel && hap run -n octopus_kernel -- og_kernel_rpc_server

echo "start agent"
cd ${ROOT_DIR}/agent && hap run -n octopus_agent -- og_agent_rpc_server

sleep 3

AGENT_RPC_KEY=$(cat ${ROOT_DIR}/agent/.env | grep admin_key | tr -d '\r' | cut -d "=" -f 2)
KERNEL_RPC_KEY=$(cat ${ROOT_DIR}/kernel/.env | grep rpc_key | tr -d '\r' | cut -d "=" -f 2)
og_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}
og_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}

while true
do
    hap status
    sleep 5
done

