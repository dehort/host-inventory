import os
import time
import grpc
import uuid

from hbi import hbi_pb2_grpc, hbi_pb2
from concurrent import futures
from collections import defaultdict
from itertools import chain


def adapt_ft(ft):
    d = defaultdict(dict)
    if ft:
        for fact in ft:
            d[fact.namespace][fact.key] = fact.value
    return d


class Filter(object):

    def __init__(self, canonical_facts=None, ids=None, tags=None, facts=None):
        self.ids = ids
        self.canonical_facts = canonical_facts or {}
        self.tags = tags or defaultdict(dict)
        self.facts = facts or defaultdict(dict)

    @classmethod
    def from_pb(cls, filter_):
        return cls(
            {f.key: f.value for f in filter_.canonical_facts},
            filter_.ids,
            adapt_ft(filter_.tags),
            adapt_ft(filter_.facts),
        )


class Host(object):

    def __init__(self, canonical_facts, id_=None, display_name=None, tags=None, facts=None):
        self.id = id_
        self.canonical_facts = canonical_facts
        self.display_name = display_name
        self.tags = tags or defaultdict(dict)
        self.facts = facts or defaultdict(dict)

    @classmethod
    def from_pb(cls, host):
        return cls(
            {f.key: f.value for f in host.canonical_facts},
            host.id,
            host.display_name,
            adapt_ft(host.tags),
            adapt_ft(host.facts),
        )

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return f"{self.id} -> {self.canonical_facts}; {self.facts}"

    def to_pb(self):
        facts = [hbi_pb2.Fact(namespace=namespace, key=k, value=v)
                 for namespace, facts in self.facts.items()
                 for k, v in facts.items()]

        canonical_facts = [hbi_pb2.CanonicalFact(key=k, value=v)
                           for k, v in self.canonical_facts.items()]

        return hbi_pb2.Host(id=self.id, display_name=self.display_name,
                            canonical_facts=canonical_facts,
                            facts=facts)

    def merge(self, new):
        for k, v in new.canonical_facts.items():
            self.canonical_facts[k] = v

        for namespace, d in new.facts.items():
            self.facts[namespace] = d

        self.display_name = new.display_name


class Index(object):

    def __init__(self):
        self.dict_ = {}
        self.all_hosts = set()

    def add(self, host):
        self.all_hosts.add(host)
        self.dict_[host.id] = host
        for t in host.canonical_facts.items():
            self.dict_[t] = host
        for t in chain(host.facts.items(), host.tags.items()):
            if t not in self.dict_:
                self.dict_[t] = set()
            self.dict_[t].add(host)

    def get(self, host):
        if host.id:
            h = self.dict_.get(host.id)
            if h:
                return h
            raise ValueError(f"Could not locate a host with given id {host.id}")

        for t in host.canonical_facts.items():
            h = self.dict_.get(t)
            if h:
                return h

    def apply_filter(self, f, hosts=None):
        hosts = hosts or self.all_hosts

        iterables = filter(None, (
            f.ids, f.canonical_facts.items(),
            f.facts.items(), f.tags.items()
        ))

        for i in chain(*iterables):
            v = self.dict_.get(i)
            if type(v) == set:
                yield from (i for i in v if i in hosts)
            elif v in hosts:
                yield v

    # orig *has* to be from a `get` to be safe
    def merge(self, orig, new):
        for t in orig.canonical_facts.items():
            del self.dict_[t]

        orig.merge(new)

        for t in orig.canonical_facts.items():
            self.dict_[t] = orig


class Service(object):
    def __init__(self):
        self.index = Index()

    def create_or_update(self, hosts):
        ret = []
        for h in hosts:
            if h.canonical_facts is None and h.id is None:
                raise ValueError("Must provide at least one canonical fact or the ID")

            # search the canonical_facts dict for a match
            existing_host = self.index.get(h)
            if existing_host:
                self.index.merge(existing_host, h)
            else:  # Host not found.  Create it.
                existing_host = h
                existing_host.id = uuid.uuid4().hex
                self.index.add(h)

            ret.append(existing_host)

        return ret

    def get(self, filters=None):
        if filters is None:
            return self.index.all_hosts
        elif type(filters) != list or any(type(f) != Filter for f in filters):
            raise ValueError("Query must be a list of Filter objects")
        else:
            filtered_set = None
            for f in filters:
                filtered_set = set(self.index.apply_filter(f, filtered_set))
            return list(filtered_set)


class Servicer(hbi_pb2_grpc.HostInventoryServicer):

    service = Service()

    def CreateOrUpdate(self, host_list, context):
        hosts = [Host.from_pb(h) for h in host_list.hosts]
        ret = self.service.create_or_update(hosts)
        return hbi_pb2.HostList(hosts=[h.to_pb() for h in ret])

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
