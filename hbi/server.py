from concurrent import futures

import time
import grpc
# import hbi_pb2
import hbi_pb2_grpc


class Servicer(hbi_pb2_grpc.HostInventoryServicer):

    def CreateOrUpdate(self, request, context):
        print(request)
        return request


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hbi_pb2_grpc.add_HostInventoryServicer_to_server(Servicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
