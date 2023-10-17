#! /bin/sh
#
# start_all.sh
# Copyright (C) 2023 imotai
#
# Distributed under terms of the MIT license.
#

if [ "$#" -eq 0 ]
then
  echo "No arguments supplied"
  exit 1
fi
ROOT_DIR=$1

mkdir -p ${ROOT_DIR}/kernel/ws
mkdir -p ${ROOT_DIR}/agent/db
mkdir -p ${ROOT_DIR}/agent/logs
mkdir -p ${ROOT_DIR}/kernel/config
mkdir -p ${ROOT_DIR}/kernel/logs
mkdir -p ${ROOT_DIR}/model_server/logs
chown -R octogen:octogen ${ROOT_DIR}/kernel/ws
chown -R octogen:octogen ${ROOT_DIR}/kernel/config
chown -R octogen:octogen ${ROOT_DIR}/agent/db
chown -R octogen:octogen ${ROOT_DIR}/agent/logs
chown -R octogen:octogen ${ROOT_DIR}/kernel/logs
chown -R octogen:octogen ${ROOT_DIR}/model_server/logs

cat <<EOF> /bin/start_service.sh
if [ "$2" -eq 1 ]
then
    if [ -z "$3" ]
    then
        echo "no model name" 
        exit 1
    else
        echo "start codellama with model name $3"
        mkdir -p ${ROOT_DIR}/model_server
        cd ${ROOT_DIR}/model_server && hap run -n codellama -- server -m ../model/$3  --alias codellama --host 127.0.0.1 --port 8080 >> ${ROOT_DIR}/model_server/logs/server.log 2>&1 
    fi
fi

echo "start kernel.."
cd ${ROOT_DIR}/kernel && hap run -n octogen_kernel -- og_kernel_rpc_server >> ${ROOT_DIR}/logs/kernel_rpc.log  2>&1

echo "start agent.."
cd ${ROOT_DIR}/agent && hap run -n octogen_agent -- og_agent_rpc_server >> ${ROOT_DIR}/logs/agent_rpc.log 2>&1
cd ${ROOT_DIR}/agent && hap run -n octogen_api -- og_agent_http_server >> ${ROOT_DIR}/logs/agent_http.log 2>&1

while true
do
    hap status
    sleep 10
done
EOF
su - octogen -c "bash /bin/start_service.sh"
