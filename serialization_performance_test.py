import timeit, os, sys, json

from hbi import hbi_pb2 as pb
from optparse import OptionParser
from hbi.model import Host


def createPBHost(i):
    name = f"node{i}"
    display_name = name
    account_number="12345"
    #facts = [pb.Fact(namespace="fact_namespace",key="k1", value="v1"), 
    #         pb.Fact(namespace="fact_namespace",key="k2",value="v2")]
    #canonical_facts = [pb.CanonicalFact(key="insights_uuid", value="value"),
    #                   pb.CanonicalFact(key="cf1", value="v1")]
    #tags = [pb.Fact(namespace="tag_namespace",key="k1", value="v1"), 
    #         pb.Fact(namespace="tag_namespace",key="k2",value="v2")]

    #facts = [pb.Fact(namespace="fact_namespace",key="k1", value="v1")]
    #canonical_facts = [pb.CanonicalFact(key="insights_uuid", value="value")]
    #tags = [pb.Fact(namespace="tag_namespace",key="k1", value="v1")]

    facts = {"fact_namespace:k1":"v1", "fact_namespace:k2":"v2"}
    canonical_facts = {"insights_uuid":"value", "cf1":"v1"}
    tags={"tag_namespace:k":"v", "tag_namespace:k2":"v2"}

    return pb.Host(id=f"{i}",
                   account_number=account_number,
                   display_name=display_name,
                   canonical_facts=canonical_facts,
                   tags=tags,
                   facts=facts)


def createPythonHost(i):
    name = f"node{i}"
    display_name = name
    account_number="12345"
    facts = {"fact_namespace:k1":"v1", "fact_namespace:k2":"v2"}
    canonical_facts = {"insights_uuid":"value", "cf1":"v1"}
    tags={"tag_namespace:k":"v", "tag_namespace:k2":"v2"}

    return Host(id_=f"{i}",
                account_number=account_number,
                display_name=display_name, 
                facts=facts, 
                tags=tags,
                canonical_facts=canonical_facts)


def createPBHosts(number_of_nodes):
    i = 0
    host_list = []
    while number_of_nodes > 0:
        host_list.append( createPBHost(i) )
        number_of_nodes = number_of_nodes - 1
        i = i + 1
    #print(host_list)


def createPythonHosts(number_of_nodes):
    i = 0
    host_list = []
    while number_of_nodes > 0:
        host_list.append( createPythonHost(i) )
        number_of_nodes = number_of_nodes - 1
        i = i + 1
    #print(host_list)


def testJsonHosts(number_of_nodes, block_size):
    host_list = []

    while number_of_nodes > 0:

        i = 0

        while i < block_size and number_of_nodes > 0:
            # add all hosts under the same account number
            host_list.append( createPythonHost(i) )

            number_of_nodes = number_of_nodes - 1

            i = i + 1

        json_output = json.dumps([h.to_json() for h in host_list])
        hosts_json = json.loads(json_output)
        returned_json_host_list = [Host.from_json(h) for h in hosts_json]
        assert len(host_list) == len(returned_json_host_list)

        #for i in returned_json_host_list:
        #    print(f"id: {i.id}, display_name: {i.display_name}, cf: {i.canonical_facts}, facts: {i.facts}, tags: {i.tags}")

        host_list.clear()


def testPBHosts(number_of_nodes, block_size):
    host_list = []

    while number_of_nodes > 0:

        i = 0

        while i < block_size and number_of_nodes > 0:
            host_list.append( createPBHost(i) ) 

            number_of_nodes = number_of_nodes - 1

            i = i + 1

        pb_host_list = pb.HostList(hosts=host_list)

        #print(pb_host_list.hosts)

        returned_pb_host_list = pb.HostList()

        # Comment this out to calculate object creation time
        returned_pb_host_list.ParseFromString(pb_host_list.SerializeToString())
        assert len(pb_host_list.hosts) == len(returned_pb_host_list.hosts)

        #for i in returned_pb_host_list.hosts:
        #    print(f"id: {i.id}, display_name: {i.display_name}, cf: {i.canonical_facts}, facts: {i.facts}, tags: {i.tags}")

        #print("****")
        #print(returned_pb_host_list.hosts)
        #print("****")
        #for key in returned_pb_host_list.hosts[0].facts:
        #    print( key, "=>", pb_host_list.hosts[0].facts[key])
        #for key in returned_pb_host_list.hosts[0].canonical_facts:
        #    print( key, "=>", pb_host_list.hosts[0].canonical_facts[key])
        #for key in returned_pb_host_list.hosts[0].tags:
        #    print( key, "=>", pb_host_list.hosts[0].tags[key])

        #print("fact:",pb_host_list.hosts[0].facts["fact_namespace:k1"])
        #print("fact:",returned_pb_host_list.hosts[0].facts["fact_namespace:k1"])

        host_list.clear()



def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped


if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option("-n", "--number-hosts",
                      dest="number_of_hosts",
                      type="int",
                      default=1,
                      help="Total number of hosts to add")

    parser.add_option("-b", "--block-size",
                      dest="block_size",
                      type="int",
                      default=10,
                      help="Block size to send to the server while adding hosts")

    parser.add_option("-m", "--mode",
                      dest="mode",
                      default="native",
                      type="string",
                      help="Server \"mode\" to use (native, tornado, grpc)")

    parser.add_option("-c", "--count",
                      dest="count",
                      default=1,
                      type="int",
                      help="Number of times to run the test")


    (options, args) = parser.parse_args()

    wrapped = wrapper(testPBHosts, options.number_of_hosts, options.block_size)
    timeCallTook = timeit.timeit(wrapped, number=options.count)
    print(f"Marshalled/Unmarshalled {options.number_of_hosts} ProtocolBuff hosts took ",timeCallTook/options.count)

    wrapped = wrapper(testJsonHosts, options.number_of_hosts, options.block_size)
    timeCallTook = timeit.timeit(wrapped, number=options.count)
    print(f"Marshalled/Unmarshalled {options.number_of_hosts} JSON hosts took ",timeCallTook/options.count)

    wrapped = wrapper(createPBHosts, options.number_of_hosts)
    timeCallTook = timeit.timeit(wrapped, number=options.count)
    print(f"Created {options.number_of_hosts} ProtocolBuff hosts took ",timeCallTook/options.count)

    wrapped = wrapper(createPythonHosts, options.number_of_hosts)
    timeCallTook = timeit.timeit(wrapped, number=options.count)
    print(f"Created {options.number_of_hosts} Python hosts took ",timeCallTook/options.count)

