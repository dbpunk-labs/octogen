#! /bin/sh
#
# add_endpoint.sh
# Copyright (C) 2023 ubuntu 
#
# Distributed under terms of the MIT license.
#

if [ "$#" -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi

ROOT_DIR=$1
AGENT_RPC_KEY=$(cat ${ROOT_DIR}/agent/.env | grep admin_key | tr -d '\r' | cut -d "=" -f 2)
KERNEL_RPC_KEY=$(cat ${ROOT_DIR}/kernel/.env | grep rpc_key | tr -d '\r' | cut -d "=" -f 2)
og_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}
