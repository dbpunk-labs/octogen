#! /bin/bash
#
# start_kernel.sh

echo "config_root_path=/kernel" >.env
echo "workspace=${workspace}" >>.env
echo "rpc_port=${rpc_port}" >>.env
echo "rpc_host=127.0.0.1" >>.env
echo "rpc_key=${rpc_key}" >>.env

octopus_kernel_rpc_server
