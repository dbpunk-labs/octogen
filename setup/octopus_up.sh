#! /bin/bash
#
# octopus_up.sh

# the function for show help information
function show_help() {
    cat <<help_message
Start octopus
Usage: octopus_up [SUBCOMMAND]

Flags:
  -h             Prints help information

Subcommands:
  cli            Install Octopus CLI only
  local          Install and start Octopus Agent without Docker (unsafe)
  docker-local   Install and start Octopus Agent with Docker
help_message
    return 0
}

function install_cli() {
    echo "install octopus chat..."
    pip3 install octopus_chat
    if [ $? -eq 0 ]; then
        echo "✅ Install octopus chat done"
    else
        echo "Fail to install octopus chat with command pip3 install octopus_chat"
    fi
    echo "please provide the following information to finish setup "
    mkdir -p ~/.octopus
    read -p 'Agent API Endpoint(default:https://agent.dbpunk.xyz): ' endpoint
    read -sp 'Agent API Key: ' key
    echo "api_key=${key}" >~/.octopus/config
    if [[ -z $endpoint ]]; then
        echo "endpoint=https://agent.dbpunk.xyz" >>~/.octopus/config
    else
        echo "endpoint=${endpoint}" >>~/.octopus/config
    fi
    echo ""
    octopus_ping
}

function start_unsafe_local_instance() {
    ROOT_DIR=$1
    hap kill -a
    hap clean
    cd $ROOT_DIR/agent && hap run -n octopus_agent -- octopus_agent_rpc_server
    cd ${ROOT_DIR}/kernel && hap run -n octopus_kernel -- octopus_kernel_rpc_server
    sleep 2
    AGENT_RPC_KEY=$(cat ${ROOT_DIR}/agent/.env | grep admin_key | cut -d "=" -f 2)
    KERNEL_RPC_KEY=$(cat ${ROOT_DIR}/kernel/.env | grep rpc_key | cut -d "=" -f 2)
    octopus_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}
    cd ${ROOT_DIR}
    hap status
    octopus_ping
}

function request_codellama_opt() {
    ROOT_DIR=$1
    read -p 'LlamaCpp Server Endpoint: ' llama_endpoint
    if [[ -z $llama_endpoint ]]; then
        echo "empty llama_endpoint"
        exit 1
    fi
    echo "llama_api_key=empty" >>${ROOT_DIR}/agent/.env
    echo "llama_api_base=${llama_endpoint}" >>${ROOT_DIR}/agent/.env
    echo "llm_key=codellama" >>${ROOT_DIR}/agent/.env
    echo "✅ Add codellama config to agent"
}

function request_openai_opt() {
    ROOT_DIR=$1
    MODEL_NAME="gpt-3.5-turbo-16k-0613"
    read -p 'OpenAI Model Name(default:gpt-3.5-turbo-16k-0613): ' new_model_name
    if [[ ! -z $new_model_name ]]; then
        MODEL_NAME=${new_model_name}
    fi
    read -sp 'OpenAI API Key: ' OPENAI_KEY
    if [[ -z $OPENAI_KEY ]]; then
        echo "empty openai key"
        exit 1
    fi
    echo ""
    echo "openai_api_key=${OPENAI_KEY}" >>${ROOT_DIR}/agent/.env
    echo "openai_api_model=${MODEL_NAME}" >>${ROOT_DIR}/agent/.env
    echo "llm_key=openai" >>${ROOT_DIR}/agent/.env
    echo "✅ Add OpenAI config to agent"
}

function request_azure_openai_opt() {
    ROOT_DIR=$1
    MODEL_NAME="gpt-3.5-turbo-16k-0613"
    read -p 'Azure API Deployment: ' AZURE_API_DEPLOYMENT
    if [[ -z $AZURE_API_DEPLOYMENT ]]; then
        echo "empty azure api base"
        exit 1
    fi
    read -p 'Azure API Base: ' AZURE_API_BASE
    if [[ -z $AZURE_API_BASE ]]; then
        echo "empty azure api base"
        exit 1
    fi
    read -sp 'Azure API Key: ' AZURE_API_KEY
    if [[ -z $AZURE_API_KEY ]]; then
        echo "empty openai key"
        exit 1
    fi
    echo ""
    echo "llm_key=azure_openai" >>${ROOT_DIR}/agent/.env
    echo "openai_api_type=azure" >>${ROOT_DIR}/agent/.env
    echo "openai_api_version=2023-07-01-preview" >>${ROOT_DIR}/agent/.env
    echo "openai_api_key=${AZURE_API_KEY}" >>${ROOT_DIR}/agent/.env
    echo "openai_api_base=${AZURE_API_BASE}" >>${ROOT_DIR}/agent/.env
    echo "openai_api_deployment=${AZURE_API_DEPLOYMENT}" >>${ROOT_DIR}/agent/.env
    echo "✅ Add Azure OpenAI config to agent"
}

function generate_common_env() {
    ROOT_DIR=$1
    password_length=32
    if [[ "$OSTYPE" == "darwin"* ]]; then
        KERNEL_KEY=$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*()-+' </dev/urandom | head -c $password_length)
        AGENT_ADMIN_KEY=$(LC_ALL=C tr -dc 'A-Za-z0-9!@#$%^&*()-+' </dev/urandom | head -c $password_length)
    else
        KERNEL_KEY=$(tr -dc 'A-Za-z0-9!@#$%^&*()-+' </dev/urandom | head -c $password_length)
        AGENT_ADMIN_KEY=$(tr -dc 'A-Za-z0-9!@#$%^&*()-+' </dev/urandom | head -c $password_length)
    fi
    mkdir -p ${ROOT_DIR}/agent
    mkdir -p ${ROOT_DIR}/kernel/ws
    mkdir -p ${ROOT_DIR}/kernel/config
    echo "config_root_path=${ROOT_DIR}/kernel/config" >${ROOT_DIR}/kernel/.env
    echo "workspace=${ROOT_DIR}/kernel/ws" >>${ROOT_DIR}/kernel/.env
    echo "rpc_host=127.0.0.1" >>${ROOT_DIR}/kernel/.env
    echo "rpc_port=9527" >>${ROOT_DIR}/kernel/.env
    echo "rpc_key=${KERNEL_KEY}" >>${ROOT_DIR}/kernel/.env

    echo "rpc_host=127.0.0.1" >${ROOT_DIR}/agent/.env
    echo "rpc_port=9528" >>${ROOT_DIR}/agent/.env
    echo "admin_key=${AGENT_ADMIN_KEY}" >>${ROOT_DIR}/agent/.env
    echo "max_file_size=10240000" >>${ROOT_DIR}/agent/.env
    echo "verbose=True" >>${ROOT_DIR}/agent/.env
    echo "db_path=${ROOT_DIR}/agent/octopus.db" >>${ROOT_DIR}/agent/.env
    echo "install the octopus"
    echo "✅ Install octopus to dir ${ROOT_DIR} done"
    if [ -f $HOME/.octopus/config ]; then
        echo "backup the old cli config to $HOME/.octopus/config.bk"
        cp $HOME/.octopus/config $HOME/.octopus/config.bk
    fi
    echo "endpoint=127.0.0.1:9528" >$HOME/.octopus/config
    echo "api_key=${KERNEL_KEY}" >>$HOME/.octopus/config
    echo "✅ Update octopus cli config done"
}

function install_octopus_package() {
    pip3 install octopus_agent octopus_kernel hapless octopus_chat
}

function install_unsafe_local_openai() {
    ROOT_DIR=$1
    generate_common_env ${ROOT_DIR}
    request_openai_opt ${ROOT_DIR}
}

function install_unsafe_local_azure_openai() {
    ROOT_DIR=$1
    generate_common_env ${ROOT_DIR}
    request_azure_openai_opt ${ROOT_DIR}
}

function install_unsafe_local_codellama() {
    ROOT_DIR=$1
    generate_common_env ${ROOT_DIR}
    request_codellama_opt ${ROOT_DIR}
}

function start_unsafe_local() {
    ROOT_DIR="$HOME/.octopus/app"
    if [ -f ${ROOT_DIR}/agent/.env ]; then
        echo "✅ You have setup the environment, the dir is ${ROOT_DIR}"
        start_unsafe_local_instance ${ROOT_DIR}
        exit 0
    fi
    read -p 'Please specify the install folder(default:~/octopus/app): ' new_dir
    if [[ ! -z $new_dir ]]; then
        ROOT_DIR=${new_dir}
    fi
    mkdir -p ${ROOT_DIR}
    if [ $? -eq 0 ]; then
        echo "✅ Create octopus app dir ${ROOT_DIR} done "
    else
        echo "❌ Create octopus app dir failed"
        exit 1
    fi
    PS3='Please enter your LLM choice number: '
    options=("OpenAI" "Azure OpenAI" "Codellama" "Quit")
    select opt in "${options[@]}"; do
        case $opt in
        "OpenAI")
            install_unsafe_local_openai ${ROOT_DIR}
            start_unsafe_local_instance ${ROOT_DIR}
            exit 0
            ;;
        "Azure OpenAI")
            install_unsafe_local_azure_openai ${ROOT_DIR}
            start_unsafe_local_instance ${ROOT_DIR}
            exit 0
            ;;
        "Codellama")
            install_unsafe_local_codellama ${ROOT_DIR}
            start_unsafe_local_instance ${ROOT_DIR}
            exit 0
            ;;
        "Quit")
            exit 0
            ;;
        *) echo "invalid option $REPLY" ;;
        esac
    done
}

# Parse the command lines
function get_opts() {
    while getopts ":h" opt; do
        case "${opt}" in
        h)
            #  Display help.
            show_help
            exit 0
            ;;
        \?)
            echo "bad options"
            exit 1
            ;;
        esac
    done
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    major_version=$(echo $python_version | awk -F. '{print $1}')
    minor_version=$(echo $python_version | awk -F. '{print $2}')
    if [[ "$major_version" -ge 3 ]] && [[ "$minor_version" -ge 9 ]]; then
        echo "Python version matchs the requirement"
    else
        echo "Python version is less than 3.9. Please upgrade your python version"
        exit 1
    fi
    shift $((OPTIND - 1))
    # Remove the main command from the argument list.
    local -r _subcommand="${1:-}"
    if [[ -z ${_subcommand} ]]; then
        show_help
        exit 0
    fi
    shift
    case "${_subcommand}" in
    cli)
        install_cli
        ;;
    local)
        start_unsafe_local
        ;;
    docker-local)
        start_localnet
        ;;
    *)
        # Unrecognized option, get help.
        echo "Invalid subcommand: ${_subcommand}!"
        show_help
        ;;
    esac
    return 0
}

function main() {
    get_opts "${@}"
    return 0
}

main "${@}"
