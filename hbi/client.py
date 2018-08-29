import os
import grpc
from hbi import hbi_pb2 as pb
from hbi import hbi_pb2_grpc, util
from hbi.model import Host

HOST = os.environ.get("HOST_INVENTORY_SERVICE_HOST", "localhost")
PORT = os.environ.get("HOST_INVENTORY_SERVICE_PORT", "50051")


class Client(object):

    def __init__(self, host=HOST, port=PORT, channel=None):
        """
        Choose to init the client with either host/port or with a
        pre-initialized channel.  Channel param is checked before host/port.
        """
        if channel:
            self.channel = channel
        else:
            self.channel = grpc.insecure_channel(f"{host}:{port}")

        self.stub = hbi_pb2_grpc.HostInventoryStub(self.channel)

    def create_or_update(self, hosts):
        host_list = pb.HostList(hosts=[h.to_pb() for h in hosts])
        response = self.stub.CreateOrUpdate(host_list)
        return [Host.from_pb(h) for h in response.hosts]

    def get(self, filters=None):
        filter_list = [f.to_pb() for f in filters] if filters else None
        response = self.stub.Get(pb.FilterList(filters=filter_list))
        return [Host.from_pb(h) for h in response.hosts]


def run():
    stub = Client()
    for name in util.names():
        display_name = "-".join(name)
        facts = {"demo": {"hostname": f"{display_name}"}}
        stub.create_or_update(Host(display_name=display_name, facts=facts))


if __name__ == "__main__":
    run()
