#
# Makefile
# jackwang, 2023-08-25 12:24
#

PROTO_PATH = ./src/octopus_proto/
PROTOS	:= $(shell find ${PROTO_PATH} -name '*.proto')
generate: $(PROTOS)
	@python3 -m grpc_tools.protoc --python_out=./src/octopus_proto \
		    --grpc_python_out=./src/octopus_proto \
			--pyi_out=./src/octopus_proto \
			--proto_path $(PROTO_PATH) \
			$^
	@sed -i 's/import kernel_server_pb2 as kernel__server__pb2/from . import kernel_server_pb2 as kernel__server__pb2/' src/octopus_proto/kernel_server_pb2_grpc.py
	@sed -i 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/octopus_proto/kernel_server_pb2_grpc.py
	@sed -i 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/octopus_proto/kernel_server_pb2.py
	@sed -i 's/import agent_server_pb2 as agent__server__pb2/from . import agent_server_pb2 as agent__server__pb2/' src/octopus_proto/agent_server_pb2_grpc.py
	@sed -i 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/octopus_proto/agent_server_pb2_grpc.py
	@sed -i 's/import common_pb2 as common__pb2/from . import common_pb2 as common__pb2/' src/octopus_proto/agent_server_pb2.py
	@echo "'${@}' done"

clean:
	@rm src/octopus_proto/*.py
	@rm src/octopus_proto/*.pyi
