import time
import grpc
import uuid

from hbi import hbi_pb2_grpc, hbi_pb2
from concurrent import futures
from collections import defaultdict


class HostAdapter(object):

    def __init__(self, host):
        self.host = host
        self.id = host.id
        self.canonical_facts = {f.key: f.value for f in host.canonical_facts}
        self.facts = self._adapt_facts()

    def _adapt_facts(self):
        d = defaultdict(dict)
        for fact in self.host.facts:
            d[fact.namespace][fact.key] = fact.value
        return d

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def to_host(self):
        facts = [hbi_pb2.Fact(namespace=namespace, key=k, value=v)
                 for namespace, facts in self.facts.items()
                 for k, v in facts.items()]

        canonical_facts = [hbi_pb2.CanonicalFact(key=k, value=v)
                           for k, v in self.canonical_facts.items()]

        return hbi_pb2.Host(id=self.id, display_name=self.host.display_name,
                            canonical_facts=canonical_facts,
                            facts=facts)

    def merge(self, new):
        for k, v in new.canonical_facts.items():
            self.canonical_facts[k] = v

        for namespace, d in new.facts.items():
            self.facts[namespace] = d


class Index(object):

    def __init__(self):
        self.dict_ = {}

    def add(self, host_adapter):
        self.dict_[host_adapter.id] = host_adapter
        for t in host_adapter.canonical_facts.items():
            self.dict_[t] = host_adapter

    def get(self, host_adapter):
        if host_adapter.id:
            h = self.dict_.get(host_adapter.id)
            if h:
                return h
            raise ValueError(f"Could not locate a host with given id {host_adapter.id}")

        for t in host_adapter.canonical_facts.items():
            h = self.dict_.get(t)
            if h:
                return h

    def merge(self, orig, new):
        for t in orig.canonical_facts.items():
            del self.dict_[t]

        orig.merge(new)

        for t in orig.canonical_facts.items():
            self.dict_[t] = orig


class Servicer(hbi_pb2_grpc.HostInventoryServicer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = Index()
        self.host_keys = defaultdict(set)

    def CreateOrUpdate(self, host_list, context):
        new_host_list = []
        for host in host_list.hosts:
            if host.canonical_facts is None and host.id is None:
                raise ValueError("Must provide at least one canonical fact or the ID")

            h = HostAdapter(host)

            # search the canonical_facts dict for a match
            existing_host = self.index.get(h)
            if existing_host:
                self.index.merge(existing_host, h)
            else:  # Host not found.  Create it.
                existing_host = h
                existing_host.id = uuid.uuid4().hex
                self.index.add(h)

            new_host_list.append(existing_host.to_host())

        return hbi_pb2.HostList(hosts=new_host_list)

    def Get(self, host_list, context):
        result = hbi_pb2.HostList()

        for host in host_list.hosts:
            match = None
            for fact in host.canonical_facts:
                fact_string = "=".join(fact.key, fact.value)
                m = self.canonical_facts.get(fact_string)

                if m is None or m != match:
                    match = None
                    break

                match = m

            if match:
                result.hosts.append(match)


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
