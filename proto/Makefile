# SPDX-FileCopyrightText: 2023 imotai <jackwang@octogen.dev>
# SPDX-FileContributor: imotai
#
# SPDX-License-Identifier: Elastic-2.0

#
# Makefile
# jackwang, 2023-08-25 12:24
#

PROTO_PATH = ./src/og_proto/
PROTOS	:= $(shell find ${PROTO_PATH} -name '*.proto')
generate: $(PROTOS)
	@python3 -m grpc_tools.protoc --python_out=./src/og_proto \
		    --grpc_python_out=./src/og_proto \
			--pyi_out=./src/og_proto \
			--proto_path $(PROTO_PATH) \
			$^
	@sed -i'' -e 's/import kernel_server_pb2 as kernel__server__pb2/from . import kernel_server_pb2 as kernel__server__pb2/' src/og_proto/kernel_server_pb2_grpc.py
	@sed -i'' -e 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/og_proto/kernel_server_pb2_grpc.py
	@sed -i'' -e 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/og_proto/kernel_server_pb2.py
	@sed -i'' -e 's/import agent_server_pb2 as agent__server__pb2/from . import agent_server_pb2 as agent__server__pb2/' src/og_proto/agent_server_pb2_grpc.py
	@sed -i'' -e 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/og_proto/agent_server_pb2_grpc.py
	@sed -i'' -e 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/og_proto/agent_server_pb2.py
	@echo "'${@}' done"

clean:
	@rm src/og_proto/*_pb2.py
	@rm src/og_proto/*_pb2_grpc.py
	@rm src/og_proto/*.pyi
