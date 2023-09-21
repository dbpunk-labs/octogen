#! /bin/bash

mkdir -p ~/.octopus/bin
mkdir -p ~/.octopus/setup
VERSION=`curl -s https://api.github.com/repos/dbpunk-labs/octopus/releases/latest | python3  -c 'import sys, json; print(json.load(sys.stdin)["name"])'`
curl -L --max-redirs 10 https://github.com/dbpunk-labs/octopus/releases/download/${VERSION}/octopus_setup-${VERSION}.tar.gz -o /tmp/octopus_setup.tar.gz
mkdir -p /tmp/octopus_setup
cd /tmp/octopus_setup && tar -zxf ../octopus_setup.tar.gz && cp -rf setup ~/.octopus/ && mv setup/octopus_up.sh ~/.octopus/bin/octopus_up
chmod +x ~/.octopus/bin/octopus_up
if [ -f ~/.zshrc ]; then
    read -p "Add ~/.octopus/bin to your PATH(y/n)? " yn
    case $yn in
        [Yy]* ) echo "PATH=~/.octopus/bin:\$PATH" >> ~/.zshrc && echo "please run source ~/.zshrc manually";;
        [Nn]* ) echo "please add PATH=~/.octopus/bin:\$PATH to ~/.zshrc manually";;
    esac
elif [ -f ~/.bashrc ]; then
    read -p "Add ~/.octopus/bin to your PATH(y/n)? " yn
    case $yn in
        [Yy]* ) echo "PATH=~/.octopus/bin:\$PATH" >> ~/.zshrc && echo "please run source ~/.bashrc manually";;
        [Nn]* ) echo "please add PATH=~/.octopus/bin:\$PATH to ~/.bashrc manually";;
    esac
else
    echo "please add PATH=~/.octopus/bin:\$PATH to your enviroment manually"
fi
echo "install octopus_up successfully"
export PATH=~/.octopus/bin:$PATH
echo "start to install octopus"
octopus_up
