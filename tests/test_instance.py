import os
import threading

from tretlager.core import instance


def test_forward_without_running_instance():
    assert instance.forward("show", name=f"\0tretlager-test-none-{os.getpid()}") is False


def test_second_call_reaches_first_instance():
    name = f"\0tretlager-test-{os.getpid()}"
    got = []
    done = threading.Event()
    srv = instance.listen(lambda c: (got.append(c), done.set()), name=name)
    try:
        assert instance.forward("start", name=name) is True
        assert done.wait(2) and got == ["start"]
        done.clear()
        assert instance.forward("rm -rf", name=name) is True  # unknown commands are ignored
        assert not done.wait(0.3)
    finally:
        srv.close()
