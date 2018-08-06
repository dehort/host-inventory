#!/usr/bin/env sh
python -m grpc_tools.protoc -I. --python_out=hbi --grpc_python_out=hbi hbi.proto
