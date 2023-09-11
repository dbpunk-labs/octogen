#! /bin/sh
#
# clean_sandbox.sh
# Copyright (C) 2023 jackwang <jackwang@jackwang-ub>
#
# Distributed under terms of the MIT license.
#


ps -eu | grep python3 | grep -v grep | awk '{print $2}' | while read line; do kill -9 $line; done
