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
    assert setup.game_version(tmp_path / "fehlt") == ""


def test_verb_weights_cover_all_verbs():
    assert set(setup.VERB_WEIGHT) == set(setup.VERBS) and sum(setup.VERB_WEIGHT.values()) == 100


def test_run_setup_skips_done_and_stops_on_error():
    class Done(setup.Step):
        id = "a"
        def done(self, ctx): return True

    class Fails(setup.Step):
        id = "b"
        def done(self, ctx): return False
        def run(self, ctx): raise setup.SetupError("kaputt")

    class Never(setup.Step):
        id = "c"
        def done(self, ctx): raise AssertionError("darf nicht laufen")

    calls = []
    old = setup.STEPS
    setup.STEPS = [Done(), Fails(), Never()]
    try:
        ok = setup.run_setup(setup.Context(), lambda i, s, t: calls.append((i, s, t)))
    finally:
        setup.STEPS = old
    assert not ok
    assert calls == [("a", "skipped", "schon erledigt"), ("b", "running", ""), ("b", "error", "kaputt")]
