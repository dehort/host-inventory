#!/usr/bin/env sh

pipenv run ./build.sh
pipenv run python3 -m hbi.server.grpc_server
