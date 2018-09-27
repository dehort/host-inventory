import grpc
import os
import time

from concurrent import futures

from hbi import hbi_pb2_grpc, hbi_pb2
from hbi.model import Host, Filter

from hbi.server import Service


class Servicer(hbi_pb2_grpc.HostInventoryServicer):

    def __init__(self):
        self.service = Service()

    def CreateOrUpdate(self, host_list, context):
        #ret = self.service.create_or_update(hosts_list.host)
        #return hbi_pb2.HostList(hosts=ret)
        print(host_list)
        return host_list

    def Get(self, filter_list, context):
        filters = [Filter.from_pb(f) for f in filter_list.filters]
        ret = self.service.get(filters)
        return hbi_pb2.HostList(hosts=[h.to_pb() for h in ret])


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hbi_pb2_grpc.add_HostInventoryServicer_to_server(Servicer(), server)
    server.add_insecure_port(f'[::]:{os.environ.get("PORT", "50051")}')
    server.start()
    return server


if __name__ == "__main__":
    server = serve()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
