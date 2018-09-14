import timeit, os
from hbi.client import Client, TornadoClient
from hbi import util
from pytest import fixture
from hbi.model import Host, Filter
from hbi.server import Service

MODE = os.environ.get("MODE", "").lower()


if MODE == "grpc":
    import grpc
    from hbi.client import Client
    print("Running in gRPC mode")

if MODE == "tornado":
    from hbi.client import TornadoClient
    print("Running in REST mode")


def createClient():
    if MODE == "grpc":
        return Client(host="localhost", port="50051")
    elif MODE == "tornado":
        return TornadoClient(host="localhost", port="8080")
    elif MODE == "native":
        return Service()
    else:
        raise RuntimeError("The MODE envrionment property was not set")


def addHosts(number_of_nodes, block_size):
    stub = createClient()
    host_list = []

    while number_of_nodes > 0:

        i = 0

        while i < block_size and number_of_nodes > 0:
            name = f"node{number_of_nodes}"
            display_name = name
            facts = {"demo": {"hostname": f"{display_name}"}}
            canonical_facts = {'insights_uuid': display_name}
            host_list.append( Host(display_name=display_name, facts=facts, canonical_facts=canonical_facts, account_number='1') )

            number_of_nodes = number_of_nodes - 1

            i = i + 1

        print("** adding hosts:",len(host_list))
        stub.create_or_update(host_list)
        host_list.clear()


def getHosts(filter_list):
    stub = createClient()

    #print(filter_list)

    host_list = stub.get(filter_list)

    #print(host_list)


def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped


if __name__ == "__main__":
    block_size=100
    number_of_nodes=1009
    wrapped = wrapper(addHosts, number_of_nodes, block_size)
    timeCallTook = timeit.timeit(wrapped, number=1)
    print(f"Added {number_of_nodes} hosts using block size of {block_size} took {timeCallTook}")


    wrapped = wrapper(getHosts, [Filter(facts = {"demo": {"hostname": f"node1"}})])
    timeCallTook = timeit.timeit(wrapped, number=10)
    print(f"Get single host x 10 took {timeCallTook}")


    wrapped = wrapper(getHosts, [Filter(account_numbers='1')])
    timeCallTook = timeit.timeit(wrapped, number=10)
    print(f"Get multiple host x 10 took {timeCallTook}")
