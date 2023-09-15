#! /bin/sh
#
# build_package.sh



WORKDIR=`pwd`
VERSION=$1
echo $VERSION
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" proto/setup.py
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" agent/setup.py
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" kernel/setup.py
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" chat/setup.py
echo "the proto new version"
python3 proto/setup.py --version
echo "the kernel new version"
python3 kernel/setup.py --version
echo "the agent new version"
python3 agent/setup.py --version
echo "the chat new version"
python3 chat/setup.py --version
# build octopus proto package
cd ${WORKDIR}/proto  && make && python3 -m build
# build octopus kernel package
cd ${WORKDIR}/kernel && python3 -m build
# build agent package
cd ${WORKDIR}/agent && python3 -m build
# build chat package
cd ${WORKDIR}/chat && python3 -m build
