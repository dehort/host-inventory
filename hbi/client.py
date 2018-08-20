import os
import grpc
from hbi.hbi_pb2 import Host, HostList, Fact
from hbi import hbi_pb2_grpc, util

host = os.environ.get("HOST_INVENTORY_SERVICE_HOST", "localhost")

def run():
    with grpc.insecure_channel(f'{host}:50051') as channel:
        stub = hbi_pb2_grpc.HostInventoryStub(channel)
        for name in util.names():
            display_name = "-".join(name)
            host_fact = Fact(namespace="demo", key="hostname", value=f"{display_name}.com")
            stub.CreateOrUpdate(HostList(hosts=[
                Host(display_name=display_name, facts=[
                    host_fact,
                ])
            ]))


if __name__ == "__main__":
    run()
