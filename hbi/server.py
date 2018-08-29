import os
import time
import grpc
import uuid

from concurrent import futures
from itertools import chain

from hbi import hbi_pb2_grpc, hbi_pb2
from hbi.model import Host, Filter


def flat_fact_chain(f):
    return chain.from_iterable(v.items() for v in f.values())


class Index(object):

    def __init__(self):
        self.dict_ = {}
        self.all_hosts = set()

    def add(self, host):
        self.all_hosts.add(host)
        self.dict_[host.id] = host
        for t in host.canonical_facts.items():
            self.dict_[t] = host
        # TODO: Actually USE the namespaces
        f_chain = flat_fact_chain(host.facts)
        t_chain = flat_fact_chain(host.tags)
        for t in chain(f_chain, t_chain):
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

        # TODO: Actually USE the fact & tag namespaces
        iterables = filter(None, (
            f.ids, f.canonical_facts.items(),
            flat_fact_chain(f.facts),
            flat_fact_chain(f.tags)
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

        # TODO: update index dict for facts and tags
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
        if not filters:
            return list(self.index.all_hosts)
        elif type(filters) != list or any(type(f) != Filter for f in filters):
            raise ValueError("Query must be a list of Filter objects")
        else:
            filtered_set = None
            for f in filters:
                filtered_set = set(self.index.apply_filter(f, filtered_set))
            return list(filtered_set or set())


class Servicer(hbi_pb2_grpc.HostInventoryServicer):

    def __init__(self):
        self.service = Service()

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
