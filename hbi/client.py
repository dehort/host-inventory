import grpc
import hbi_pb2
import hbi_pb2_grpc


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hbi_pb2_grpc.HostInventoryStub(channel)
        stub.Create(hbi_pb2.Host(display_name="boinga"))


if __name__ == "__main__":
    run()
