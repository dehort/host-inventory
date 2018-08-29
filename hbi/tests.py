import os
import grpc

from hbi.server import Host, Filter, Service, serve
from hbi.util import names
from hbi.client import Client
from pytest import fixture

GRPC = os.environ.get("GRPC", "false").lower() == "true"


@fixture
def service():
    if GRPC:
        server = serve()
        server.service = Service()
        connect_str = f"localhost:{os.environ.get('PORT', '50051')}"
        with grpc.insecure_channel(connect_str) as ch:
            yield Client(channel=ch)
        server.stop(0)
    else:
        yield Service()


@fixture
def host_list():
    return [Host({"hostname": n}, display_name=f"{n}.com")
            for n in ("-".join(dn) for dn in names())]


def test_create(service, host_list):
    ret_hostnames = {h.canonical_facts["hostname"]
                     for h in service.create_or_update(host_list)}
    original_hostnames = {h.canonical_facts["hostname"] for h in host_list}
    assert ret_hostnames == original_hostnames


def test_update(service):
    host = Host({
        "insights_id": "1234",
        "hostname": "inventory-test.redhat.com"
    })

    service.create_or_update([host])

    host = Host({
        "hostname": "inventory-test.redhat.com"
    }, facts={
        "advisor": {"cpu.count": "4"}
    })

    def validate(ret):
        assert ret.facts["advisor"]["cpu.count"] == "4"
        assert ret.canonical_facts["hostname"] == "inventory-test.redhat.com"
        assert ret.canonical_facts["insights_id"] == "1234"

    host = service.create_or_update([host])[0]
    validate(host)
    validate(service.get([Filter(ids=[host.id])])[0])


def test_get_all(service, host_list):
    service.create_or_update(host_list)
    ret_hosts = service.get()
    assert len(ret_hosts) == len(host_list)
    assert set(r.display_name for r in ret_hosts) == set(h.display_name for h in host_list)


def test_create_and_get(service, host_list):
    r = service.create_or_update(host_list)
    ret_hosts = service.get([Filter(ids=[r[0].id])])
    assert len(ret_hosts) == 1


def test_get_one(service, host_list):
    filters = Filter(ids=[service.create_or_update(host_list)[0].id])
    assert len(service.get([filters])) == 1


def test_get_fact(service):
    facts = {"ns": {"host": "test"}}
    h = Host({"insights_id": "a"}, facts=facts)
    service.create_or_update([h])
    r = service.get([Filter(facts=facts)])
    assert len(r) == 1


def test_get_tag(service):
    tags = {"ns": {"env": "prod"}}
    h = Host({"insights_id": "a"}, tags=tags)
    service.create_or_update([h])
    r = service.get([Filter(tags=tags)])
    assert len(r) == 1
