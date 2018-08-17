from hbi.server import Servicer, Host, Service
from hbi.hbi_pb2 import HostList, CanonicalFact
from hbi.util import names
import hbi.hbi_pb2 as p


def test_create():
    host_list = [Host({"hostname": n}, display_name=f"{n}.com")
                 for n in ("-".join(dn) for dn in names())]
    ret_hostnames = {h.canonical_facts["hostname"]
                     for h in Service().create_or_update(host_list)}
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


def test_update():
    service = Service()
    host = Host({
        "insights_id": "1234",
        "hostname": "inventory-test.redhat.com"
    })

    next(service.create_or_update([host]))

    host = Host({
        "hostname": "inventory-test.redhat.com"
    })

    host.facts["advisor"]["cpu.count"] = "4"

    ret = next(service.create_or_update([host]))
    assert ret.facts["advisor"]["cpu.count"] == "4"
    assert ret.canonical_facts["hostname"] == "inventory-test.redhat.com"
    assert ret.canonical_facts["insights_id"] == "1234"
