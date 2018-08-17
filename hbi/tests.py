import hbi.hbi_pb2 as p

from hbi.server import Servicer, Host, Service
from hbi.hbi_pb2 import HostList, CanonicalFact
from hbi.util import names
from pytest import fixture


@fixture
def service():
    return Service()


def gen_host_list():
    return [Host({"hostname": n}, display_name=f"{n}.com")
            for n in ("-".join(dn) for dn in names())]


def test_create(service):
    host_list = gen_host_list()
    ret_hostnames = {h.canonical_facts["hostname"]
                     for h in service.create_or_update(host_list)}
    original_hostnames = {h.canonical_facts["hostname"] for h in host_list}
    assert ret_hostnames == original_hostnames


def test_servicer():
    host_list = HostList(hosts=[
        p.Host(
            display_name="-".join(display_name),
            canonical_facts=[
                CanonicalFact(
                    key="hostname",
                    value=f"{'-'.join(display_name)}.com",
                )
            ]) for display_name in names()
    ])

    service = Servicer()
    ret = service.CreateOrUpdate(host_list, None)
    assert len(ret.hosts) == len(host_list.hosts)
    assert host_list.hosts[0].display_name == ret.hosts[0].display_name
    assert len(service.Get(HostList(hosts=ret.hosts[:1]), None).hosts) == 1


def test_update(service):
    host = Host({
        "insights_id": "1234",
        "hostname": "inventory-test.redhat.com"
    })

    service.create_or_update([host])

    host = Host({
        "hostname": "inventory-test.redhat.com"
    })

    host.facts["advisor"]["cpu.count"] = "4"

    ret = service.create_or_update([host])[0]
    assert ret.facts["advisor"]["cpu.count"] == "4"
    assert ret.canonical_facts["hostname"] == "inventory-test.redhat.com"
    assert ret.canonical_facts["insights_id"] == "1234"


def test_get_all(service):
    hosts = gen_host_list()
    service.create_or_update(hosts)
    assert sum(1 for _ in service.get()) == len(hosts)


def test_get_one(service):
    hosts = gen_host_list()
    host = list(service.create_or_update(hosts))[:1]
    assert sum(1 for _ in service.get(host)) == 1
