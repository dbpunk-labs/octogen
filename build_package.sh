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
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" up/setup.py
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\",/version=\"$VERSION\",/g" sdk/setup.py
echo "the proto new version"
python3 proto/setup.py --version
echo "the kernel new version"
python3 kernel/setup.py --version
echo "the agent new version"
python3 agent/setup.py --version
echo "the chat new version"
python3 chat/setup.py --version
echo "the up new version"
python3 up/setup.py --version
echo "the sdk new version"
python3 sdk/setup.py --version
# build octopus proto package
cd ${WORKDIR}/proto  && make && python3 -m build
# build octopus proto package
cd ${WORKDIR}/sdk && python3 -m build
# build octopus kernel package
cd ${WORKDIR}/kernel && python3 -m build
# build agent package
cd ${WORKDIR}/agent && python3 -m build
# build chat package
cd ${WORKDIR}/chat && python3 -m build
# build up package
cd ${WORKDIR}/up && python3 -m build
