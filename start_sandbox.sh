#! /bin/sh
# start_local.sh

ps -ef | grep python3 | grep og |grep -v grep | awk '{print $2}' | while read line; do kill -9 $line; done
WORKDIR=`pwd`
bash install_package.sh
mkdir -p ${WORKDIR}/sandbox/kernel
mkdir -p ${WORKDIR}/sandbox/agent
cd ${WORKDIR}/sandbox/kernel
KERNEL_RPC_KEY=ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH
echo ${KERNEL_RPC_KEY}
mkdir -p /tmp/ws1 /tmp/kernel_config

cat <<EOF> .env
config_root_path=/tmp/kernel_config
workspace=/tmp/ws1
rpc_host=127.0.0.1
rpc_port=9527
rpc_key=${KERNEL_RPC_KEY}
EOF

echo "start kernel with endpoint 127.0.0.1:9527"

og_kernel_rpc_server > kernel_rpc.log 2>&1 &
sleep 2

cd ${WORKDIR}/sandbox/agent
AGENT_RPC_KEY=ZCeI9cYtOCyLISoi488BgZHeBkHWuFUH
test -f /tmp/octopus_sandbox.db && rm /tmp/octopus_sandbox.db
echo "start agent with endpoint 127.0.0.1:9528"

cat <<EOF> .env
rpc_host=127.0.0.1
rpc_port=9528
admin_key=${AGENT_RPC_KEY}
llm_key=mock
max_file_size=10240000
verbose=True
db_path=/tmp/octopus_sandbox.db
cases_path=${WORKDIR}/sdk/tests/mock_messages.json
EOF

og_agent_rpc_server > agent_rpc.log 2>&1 &
og_agent_http_server > agent_http.log 2>&1 &
sleep 2
echo "add a kernel"
og_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}

mkdir -p ~/.octogen
cat <<EOF> ~/.octogen/config
endpoint=127.0.0.1:9528
api_key=${KERNEL_RPC_KEY}
EOF
og_ping
