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


def test_multiple_filters(service):
    hosts = [
        Host(
            display_name='test1.example.org',
            canonical_facts={'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF00'},
            facts={'advisor': {'account': '1234567', 'role': 'host'}},
        ),
        Host(
            display_name='test2.example.org',
            canonical_facts={'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF11'},
            facts={'advisor': {'account': '1234567', 'role': 'manager'}},
        ),
        Host(
            display_name='test1.example.net',
            canonical_facts={'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF22'},
            facts={'advisor': {'account': '1122334', 'role': 'host'}},
        ),
        Host(
            display_name='test2.example.net',
            canonical_facts={'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF33'},
            facts={'advisor': {'account': '1122334', 'role': 'manager'}},
        ),
    ]
    hosts_added = service.create_or_update(hosts)
    assert isinstance(hosts_added, list)
    assert len(hosts) == len(hosts_added)
    for hostnum in range(len(hosts)):
        # Compare pb2 objects directly
        assert hosts_added[hostnum].display_name == hosts[hostnum].display_name
        assert hosts_added[hostnum].canonical_facts == hosts[hostnum].canonical_facts
        assert hosts_added[hostnum].facts == hosts[hostnum].facts

    # We should be able to get one host by a single filter on ID.
    hf1 = service.get(filters=[
        Filter(ids=[hosts_added[0].id])
    ])
    assert isinstance(hf1, list)
    assert len(hf1) == 1
    assert hf1[0].display_name == hosts[0].display_name

    # We should be able to get one host by a single filter on canonical fact.
    hf2 = service.get(filters=[
        Filter(canonical_facts={
            'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF11'
        })
    ])
    assert isinstance(hf2, list)
    assert len(hf2) == 1
    assert hf2[0].display_name == hosts[1].display_name

    # We should be able to get multiple hosts by a single filter on account fact.
    hf3 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1122334'}})
    ])
    assert isinstance(hf3, list)
    assert len(hf3) == 2
    # Hosts are returned in random order, so check sorted lists
    assert sorted(h.display_name for h in hf3) == sorted(h.display_name for h in hosts[2:4])

    # We should be able to get a single host by multiple filters on account facts.
    # Separate filters AND together - intersection of sets.
    hf4 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1122334'}}),
        Filter(facts={'advisor': {'role': 'host'}})
    ])
    assert isinstance(hf4, list)
    assert len(hf4) == 1
    assert hf4[0].display_name == hosts[2].display_name

    # We should be able to get a single host by multiple filters on facts and canonical_facts.
    hf5 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1234567'}}),
        Filter(canonical_facts={
            'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF11',
        })
    ])
    assert isinstance(hf5, list)
    assert len(hf5) == 1
    assert hf5[0].display_name == hosts[1].display_name

    # When multiple filters have no intersection, we should get nothing
    hf6 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1122334'}}),
        Filter(canonical_facts={
            'insights_uuid': '11223344-5566-7788-99AA-BBCCDDEEFF11'
        })
    ])
    assert isinstance(hf6, list)
    assert len(hf6) == 0

    # We should be able to get multiple hosts with a single filter that
    # looks for two separate account facts.
    # In the same filter, facts OR together - union of sets.
    hf7 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1122334', 'role': 'manager'}})
    ])
    assert isinstance(hf7, list)
    assert len(hf7) == 3
    # Hosts are returned in random order, so check sorted lists
    assert sorted(h.display_name for h in hf7) == sorted(h.display_name for h in hosts[1:4])

    # If one filter matches something that doesn't exist, and there are
    # multiple filters, we should still get nothing (canonical fact first)
    hf8 = service.get(filters=[
        Filter(canonical_facts={
            'insights_uuid': '11223344-5566-7788-99AA-000000000000'
        }),
        Filter(facts={'advisor': {'account': '1122334'}}),
    ])
    assert isinstance(hf8, list)
    assert len(hf8) == 0

    # If one filter matches something that doesn't exist, and there are
    # multiple filters, we should still get nothing (multiple fact first)
    hf9 = service.get(filters=[
        Filter(facts={'advisor': {'account': '1122334'}}),
        Filter(canonical_facts={
            'insights_uuid': '11223344-5566-7788-99AA-000000000000'
        }),
    ])
    assert isinstance(hf9, list)
    assert len(hf9) == 0


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
