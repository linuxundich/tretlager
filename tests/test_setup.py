import threading
import time

from tretlager.core import setup

OSSL = """Message digest algorithm  : SHA256
Signer's certificate:
	------------------
	Signer #0:
		Subject: jurisdictionC=US,jurisdictionST=Delaware,businessCategory=Private Organization,CN=Zwift\\, Inc.,serialNumber=5463328,O=Zwift\\, Inc.,L=Long Beach,ST=California,C=US
		Issuer : CN=SSL.com EV Code Signing Intermediate CA RSA R3,O=SSL Corp
Succeeded
"""


def test_parse_signer_and_requirements():
    signer = setup.parse_signer(OSSL)
    assert signer.startswith("jurisdictionC=US")
    assert all(part in signer for part in setup.SIGNER_REQUIRED)


def test_parse_signer_missing():
    assert setup.parse_signer("Failed") == ""


def test_parse_gltest():
    out = "ChoosePixelFormat: 25\nGL_VENDOR:   NVIDIA Corporation\nGL_RENDERER: NVIDIA GeForce RTX 3050 Ti Laptop GPU/PCIe/SSE2\nGL_VERSION:  4.6.0 NVIDIA 580.178.04\n"
    r = setup.parse_gltest(out)
    assert r == {"gl_vendor": "NVIDIA Corporation", "gl_renderer": "NVIDIA GeForce RTX 3050 Ti Laptop GPU/PCIe/SSE2",
                 "gl_version": "4.6.0 NVIDIA 580.178.04"}


def test_graphics_env():
    assert setup.graphics_env({"offload": True}) == {"__NV_PRIME_RENDER_OFFLOAD": "1",
                                                      "__GLX_VENDOR_LIBRARY_NAME": "nvidia"}
    assert setup.graphics_env({"offload": False}) == {}


def test_game_version_utf16_reference(tmp_path):
    (tmp_path / "Zwift_ver_cur_filename.txt").write_bytes("Zwift_ver_cur.167761.xml".encode("utf-16-le"))
    (tmp_path / "Zwift_ver_cur.167761.xml").write_text('<Zwift version="1.0.167761" sversion="1.124.0 (167761)"/>')
    assert setup.game_version(tmp_path) == "1.124.0 (167761)"
    assert setup.game_version(tmp_path / "missing") == ""


def test_verb_weights_cover_all_verbs():
    assert set(setup.VERB_WEIGHT) == set(setup.VERBS) and sum(setup.VERB_WEIGHT.values()) == 100


def test_run_setup_skips_done_and_stops_on_error():
    class Done(setup.Step):
        id = "a"
        def done(self, ctx): return True

    class Fails(setup.Step):
        id = "b"
        def done(self, ctx): return False
        def run(self, ctx): raise setup.SetupError("broken")

    class Never(setup.Step):
        id = "c"
        def done(self, ctx): raise AssertionError("must not run")

    calls = []
    old = setup.STEPS
    setup.STEPS = [Done(), Fails(), Never()]
    try:
        ok = setup.run_setup(setup.Context(), lambda i, s, t: calls.append((i, s, t)))
    finally:
        setup.STEPS = old
    assert not ok
    assert calls == [("a", "skipped", "already done"), ("b", "running", ""), ("b", "error", "broken")]


# --- Context.run(): waits for the process, not for the end of the pipe ---------------------------
# Wine helpers inherit the output pipe and outlive the command. Until 2026-11-13 run() read until
# end-of-file and therefore hung: after the .NET installation the setup stood still for half an hour.

def _ctx():
    lines = []
    ctx = setup.Context(log=lines.append)
    return ctx, lines


def test_run_logs_output_and_returns_code():
    ctx, lines = _ctx()
    assert ctx.run(["sh", "-c", "echo hello; echo world >&2; exit 3"], env={}) == 3
    assert "hello" in lines and "world" in lines


def test_run_returns_when_a_child_keeps_the_pipe_open(monkeypatch):
    """The command exits, a grandchild holds the pipe: run() must not wait for it."""
    monkeypatch.setattr(setup, "OUTPUT_GRACE", 0.5)
    ctx, lines = _ctx()
    started = time.monotonic()
    # The background sleep inherits stdout, so the pipe stays open for 30 s
    rc = ctx.run(["sh", "-c", "echo before; sleep 30 & exit 0"], env={}, timeout=3600)
    took = time.monotonic() - started
    assert rc == 0
    assert "before" in lines                      # output up to then is kept
    assert took < 10, f"run() waited {took:.1f} s for the pipe"


def test_run_honours_cancel():
    ctx, _lines = _ctx()
    threading.Timer(0.3, ctx.cancel.set).start()
    started = time.monotonic()
    ctx.run(["sh", "-c", "sleep 30"], env={}, timeout=3600)
    assert time.monotonic() - started < 10


def test_run_honours_timeout():
    ctx, _lines = _ctx()
    started = time.monotonic()
    ctx.run(["sh", "-c", "sleep 30"], env={}, timeout=1)
    assert time.monotonic() - started < 10
