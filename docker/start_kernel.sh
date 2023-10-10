#! /bin/sh
#
# start_kernel.sh
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
mkdir -p ${ROOT_DIR}/kernel/config
mkdir -p ${ROOT_DIR}/kernel/logs
chown -R octogen:octogen ${ROOT_DIR}/kernel/ws
chown -R octogen:octogen ${ROOT_DIR}/kernel/config
chown -R octogen:octogen ${ROOT_DIR}/kernel/logs

cat <<EOF> /bin/start_service.sh
echo "start kernel.."
cd ${ROOT_DIR}/kernel && hap run -n octopus_kernel -- og_kernel_rpc_server >>${ROOT_DIR}/kernel/logs/kernel_rpc.log 2>&1

while true
do
    hap status
    sleep 10
done
EOF
su - octogen -c "bash /bin/start_service.sh"
