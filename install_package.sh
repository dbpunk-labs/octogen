#! /bin/sh
#
# install_package.sh

WORKDIR=`pwd`
cd ${WORKDIR}/proto && make && pip install .
cd ${WORKDIR}/sdk && pip install .
cd ${WORKDIR}/kernel && pip install .
cd ${WORKDIR}/agent && pip install .
cd ${WORKDIR}/chat && pip install .
