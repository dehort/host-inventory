from hbi.server import Servicer
from hbi.hbi_pb2 import Host, HostList, Fact
from hbi.util import names


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
            ]) for display_name in names()
    ])

    assert host_list == server.CreateOrUpdate(host_list, None)
