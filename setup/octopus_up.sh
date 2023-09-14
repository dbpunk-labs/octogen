#! /bin/bash
#
# octopus_up.sh


# the function for show help information
function show_help() {
  cat <<help_message
Start octopus
Usage: octopus_up [SUBCOMMAND]

Flags:
  -h, --help     Prints help information

Subcommands:
  cli            Install Octopus CLI only
  unsafe-local   Install and start Octopus Agent without Docker (unsafe)
  docker-local   Install and start Octopus Agent with Docker
help_message
  return 0
}

function install_cli() {
    echo "install octopus chat..."
    pip3 install octopus_chat
    if [ $? -eq 0 ]
    then
      echo "✅ Install octopus chat done"
    else
      echo "Fail to install octopus chat with command pip3 install octopus_chat"
    fi
    echo "please provide the following information to finish setup "
    mkdir -p ~/.octopus
    read -p 'Agent API Endpoint(default:https://agent.dbpunk.xyz): ' endpoint
    read -sp 'Agent API Key: ' key
    echo "api_key=${key}" > ~/.octopus/config
    if [[ -z $endpoint ]]
    then
        echo "endpoint=https://agent.dbpunk.xyz" >> ~/.octopus/config
    else
        echo "endpoint=${endpoint}" >> ~/.octopus/config
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
    AGENT_RPC_KEY=`cat ${ROOT_DIR}/agent/.env| grep admin_key | cut -d "=" -f 2`
    KERNEL_RPC_KEY=`cat ${ROOT_DIR}/kernel/.env| grep rpc_key | cut -d "=" -f 2`
    octopus_agent_setup --kernel_endpoint=127.0.0.1:9527 --kernel_api_key=${KERNEL_RPC_KEY} --agent_endpoint=127.0.0.1:9528 --admin_key=${AGENT_RPC_KEY}
    cd ${ROOT_DIR}
    hap status
    octopus_ping
}

function install_unsafe_local_openai() {
    ROOT_DIR=$1
    MODEL_NAME="gpt-3.5-turbo-16k-0613"
    read -p 'OpenAI Model Name(default:gpt-3.5-turbo-16k-0613): ' new_model_name
    if [[ ! -z $new_model_name ]]
    then
        MODEL_NAME=${new_model_name}
    fi
    read -sp 'OpenAI API Key: ' OPENAI_KEY
    if [[  -z $OPENAI_KEY ]]
    then
        echo "empty openai key"
        exit 1
    fi
    echo ""
    KERNEL_KEY=`tr -dc A-Za-z0-9 </dev/urandom | head -c 32 ; echo ''`
    AGENT_ADMIN_KEY=`tr -dc A-Za-z0-9 </dev/urandom | head -c 32 ; echo ''`
    mkdir -p ${ROOT_DIR}/agent
    mkdir -p ${ROOT_DIR}/kernel/ws
    mkdir -p ${ROOT_DIR}/kernel/config

    ls ${ROOT_DIR}
    echo "config_root_path=${ROOT_DIR}/kernel/config"> ${ROOT_DIR}/kernel/.env
    echo "workspace=${ROOT_DIR}/kernel/ws">> ${ROOT_DIR}/kernel/.env
    echo "rpc_host=127.0.0.1">> ${ROOT_DIR}/kernel/.env
    echo "rpc_port=9527">> ${ROOT_DIR}/kernel/.env
    echo "rpc_key=${KERNEL_KEY}">> ${ROOT_DIR}/kernel/.env

    echo "rpc_host=127.0.0.1"> ${ROOT_DIR}/agent/.env
    echo "rpc_port=9528">> ${ROOT_DIR}/agent/.env
    echo "admin_key=${AGENT_ADMIN_KEY}">> ${ROOT_DIR}/agent/.env
    echo "llm_key=openai" >> ${ROOT_DIR}/agent/.env
    echo "openai_api_key=${OPENAI_KEY}" >> ${ROOT_DIR}/agent/.env
    echo "openai_api_model=${MODEL_NAME}" >> ${ROOT_DIR}/agent/.env
    echo "max_file_size=10240000" >>${ROOT_DIR}/agent/.env
    echo "verbose=True" >>${ROOT_DIR}/agent/.env
    echo "db_path=${ROOT_DIR}/agent/octopus.db" >>${ROOT_DIR}/agent/.env
    echo "install the octopus"
    pip3 install octopus_agent octopus_kernel hapless octopus_chat
    echo "✅ Install octopus to dir ${ROOT_DIR} done"
    if [ -f $HOME/.octopus/config ]; then
        echo "backup the old cli config to $HOME/.octopus/config.bk"
        cp $HOME/.octopus/config $HOME/.octopus/config.bk
    fi
    echo "endpoint=127.0.0.1:9528" > ~/.octopus/config
    echo "api_key=${KERNEL_KEY}" > ~/.octopus/config
    echo "✅ Update octopus cli config done"
}



function start_unsafe_local() {
    ROOT_DIR="$HOME/.octopus/app"
    if [ -f ${ROOT_DIR}/agent/.env ]; then
      echo "✅ You have setup the environment, the dir is ${ROOT_DIR}"
      start_unsafe_local_instance ${ROOT_DIR}
      exit 0
    fi
    read -p 'Please specify the install folder(default:~/octopus/app): ' new_dir
    if [[ ! -z $new_dir ]]
    then
        ROOT_DIR=${new_dir}
    fi
    mkdir -p ${ROOT_DIR}
    if [ $? -eq 0 ]
    then
      echo "✅ Create octopus app dir ${ROOT_DIR} done "
    else
      echo "❌ Create octopus app dir failed"
      exit 1
    fi
    PS3='Please enter your LLM choice: '
    options=("OpenAI" "Azure OpenAI" "Codellama" "Quit")
    select opt in "${options[@]}"
    do
        case $opt in
            "OpenAI")
                install_unsafe_local_openai ${ROOT_DIR}
                start_unsafe_local_instance ${ROOT_DIR}
                exit 0
                ;;
            "Azure OpenAI")
                echo "you chose choice 2"
                ;;
            "Codellama")
                echo "you chose choice $REPLY which is $opt"
                ;;
            "Quit")
                break
                ;;
            *) echo "invalid option $REPLY";;
        esac
    done
}

# Parse the command lines
function get_opts() {
  #  Parse options to the main command.
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
  shift $((OPTIND -1))
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
    unsafe-local)
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
