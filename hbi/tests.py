from hbi.server import Servicer, HostAdapter
from hbi.hbi_pb2 import Host, HostList, CanonicalFact
from hbi.util import names


HOST_LIST = HostList(hosts=[
    Host(
        display_name="-".join(display_name),
        canonical_facts=[
            CanonicalFact(
                key="hostname",
                value=f"{'-'.join(display_name)}.com",
            )
        ]) for display_name in names()
])


def test_create():
    ret_hosts = [HostAdapter(h) for h in Servicer().CreateOrUpdate(HOST_LIST, None).hosts]
    ret_hostnames = set(h.canonical_facts["hostname"] for h in ret_hosts)
    original_hosts = [HostAdapter(h) for h in HOST_LIST.hosts]
    original_hostnames = set(h.canonical_facts["hostname"] for h in original_hosts)
    assert ret_hostnames == original_hostnames


def gen_host(canonical_facts):
    facts = [CanonicalFact(key=k, value=v) for k, v in canonical_facts.items()]
    return Host(canonical_facts=facts)


def test_update():
    service = Servicer()
    canonical_facts = {
        "insights_id": "1234",
        "hostname": "inventory-test.redhat.com"
    }
    host = gen_host(canonical_facts)
    service.CreateOrUpdate(HostList(hosts=[host]), None)
    del canonical_facts["insights_id"]
    host = gen_host(canonical_facts)
    host.facts.add(key="cpu.count", value="4")
    ret = service.CreateOrUpdate(HostList(hosts=[host]), None)
    assert ret.hosts[0].facts[0].value == "4"
    for k, v in ((f.key, f.value) for f in ret.hosts[0].canonical_facts):
        print(k, v)
        if k == "insights_id":
            assert v == "1234"
            return
    assert False, "Failed to find insights_id"
