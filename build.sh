#!/usr/bin/env sh
python3 -m grpc_tools.protoc -I proto --python_out=hbi --grpc_python_out=hbi proto/hbi.proto
sed -i 's/import hbi/from . import hbi/' hbi/hbi_pb2_grpc.py
