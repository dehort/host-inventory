import timeit, os, sys
from hbi.client import Client, TornadoClient
from hbi import util
from pytest import fixture
from hbi.model import Host, Filter
from hbi.server import Service
from optparse import OptionParser

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

            # add all hosts under the same account number
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

    parser = OptionParser()

    parser.add_option("-s", "--server",
                      dest="host",
                      type="string",
                      help="Server name of the inventory server")

    parser.add_option("-p", "--port",
                      dest="port",
                      type="int",
                      default=50051,
                      help="Port number inventory server is listening on")

    parser.add_option("-n", "--number-hosts",
                      dest="number_of_hosts",
                      type="int",
                      default=100,
                      help="Total number of hosts to add")

    parser.add_option("-b", "--block-size",
                      dest="block_size",
                      type="int",
                      default=10,
                      help="Block size to send to the server while adding hosts")

    (options, args) = parser.parse_args()

    print(options)

    if not options.host or not options.port:
        parser.print_help()
        sys.exit(1)

    wrapped = wrapper(addHosts, options.number_of_hosts, options.block_size)
    timeCallTook = timeit.timeit(wrapped, number=1)
    print(f"Added {options.number_of_hosts} hosts using block size of {options.block_size} took {timeCallTook}")


    # simulate a simple ping
    wrapped = wrapper(getHosts, [Filter(facts = {"demo": {"hostname": f"node1"}})])
    timeCallTook = timeit.timeit(wrapped, number=10)
    print(f"Get single host x 10 took {timeCallTook}")

    
    # ask for all nodes that were added above
    wrapped = wrapper(getHosts, [Filter(account_numbers='1')])
    timeCallTook = timeit.timeit(wrapped, number=10)
    print(f"Get multiple host x 10 took {timeCallTook}")
