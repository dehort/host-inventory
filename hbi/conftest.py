from hbi.tests import MODE

if MODE == "tornado":
    from hbi.tests import loop

    def pytest_runtest_teardown(item, nextitem):
        if nextitem is None:
            loop.stop()
