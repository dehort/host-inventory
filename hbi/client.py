import grpc
from .hbi_pb2 import Host, HostList, Fact
from . import hbi_pb2_grpc
import itertools

colors = ["white", "blue", "orange", "black", "yellow", "green", "red", "taupe"]
adj = ["flippant", "dashing", "sullen", "starving", "ravishing", "sickly", "gaunt", "spry", "homely", "greasy"]
nouns = ["condor", "triangle", "notebook", "shovel", "hairbrush", "boots", "clarinet"]

names = itertools.product(colors, adj, nouns)


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hbi_pb2_grpc.HostInventoryStub(channel)
        for name in names:
            display_name = "-".join(name)
            host_fact = Fact(namespace="demo", key="hostname", value=f"{display_name}.com")
            stub.CreateOrUpdate(HostList(hosts=[
                Host(display_name=display_name, facts=[
                    host_fact,
                ])
            ]))


if __name__ == "__main__":
    run()
