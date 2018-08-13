from .server import Servicer
from .hbi_pb2 import Host, HostList, Fact
import itertools

colors = ["white", "blue", "orange", "black", "yellow", "green", "red", "taupe"]
adj = ["flippant", "dashing", "sullen", "starving", "ravishing", "sickly", "gaunt", "spry", "homely", "greasy"]
nouns = ["condor", "triangle", "notebook", "shovel", "hairbrush", "boots", "clarinet"]

names = itertools.product(colors, adj, nouns)


def test_server():
    server = Servicer()

    host_list = HostList(hosts=[
        Host(
            display_name="-".join(display_name),
            facts=[
                Fact(
                    namespace="demo",
                    key="hostname",
                    value=f"{'-'.join(display_name)}.com",
                )
            ]) for display_name in names
    ])

    assert host_list == server.CreateOrUpdate(host_list, None)
