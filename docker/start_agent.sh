#! /bin/bash
#
# start_kernel.sh

echo "rpc_port=${rpc_port}" >.env
echo "rpc_host=0.0.0.0" >>.env
echo "admin_key=${admin_key}" >>.env
echo "llm_key=${llm_key}" >> .env
echo "max_file_size=20480000" >> .env
echo "max_iterations=8" >> .env
echo "verbose=False" >> .env
if [[ ${llm_key} == "azure_openai" ]]; then
    echo "openai_api_type=${openai_api_type}" >>.env
    echo "openai_api_version=${openai_api_version}" >>.env
    echo "openai_api_base=${openai_api_base}" >> .env
    echo "openai_api_key=${openai_api_key}" >> .env
    echo "openai_api_deployment=${openai_api_deployment}" >> .env
    octopus_agent_rpc_server
else
    echo "unsupported llm key"
fi
