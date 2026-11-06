from tretlager.core import btcompat


def _adapter(root, vendor, product):
    usb = root / "usb3" / "3-10"
    iface = usb / "3-10:1.0"
    iface.mkdir(parents=True)
    (usb / "idVendor").write_text(vendor + "\n")
    (usb / "idProduct").write_text(product + "\n")
    hci = root / "hci0"
    hci.mkdir()
    (hci / "device").symlink_to(iface)


def test_adapter_chip_from_usb_interface(tmp_path):
    _adapter(tmp_path, "8087", "0026")
    chip = btcompat.adapter_chip(root=tmp_path)
    assert chip == btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")


def test_adapter_chip_without_adapter(tmp_path):
    assert btcompat.adapter_chip(root=tmp_path) is None


ISSUE = btcompat.Issue(chips=frozenset({"8087:0026"}), device=__import__("re").compile(r"^Strap"),
                       device_name="Strap", text="Strap does not like {chip}", short="Not with {chip}")


def test_known_issue_warns(monkeypatch):
    monkeypatch.setattr(btcompat, "KNOWN_ISSUES", [ISSUE])
    ax201 = btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")
    assert btcompat.issue_for(ax201, "Strap 1") == "Strap does not like Intel Wi-Fi 6 AX201"
    assert btcompat.issue_for(ax201, "Strap 1", short=True) == "Not with Intel Wi-Fi 6 AX201"
    assert btcompat.issue_for(ax201, "TICKR 9029") == ""
    assert btcompat.issue_for(btcompat.Chip("8087:0029", "Intel Wi-Fi 6 AX200"), "Strap 1") == ""
    assert btcompat.issue_for(None, "Strap 1") == ""


def test_hrm_pro_on_ax201_no_longer_warns():
    # 2026-11-06: the "hang" was the remembered slow interval; it connects with 0.11.2
    ax201 = btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")
    assert btcompat.issue_for(ax201, "HRMPro+:462237") == ""


def test_annotate_adds_field(monkeypatch):
    monkeypatch.setattr(btcompat, "KNOWN_ISSUES", [ISSUE])
    ax201 = btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")
    out = btcompat.annotate([{"name": "Strap 1"}, {"name": "Wahoo KICKR C058"}], ax201)
    assert out[0]["compat"] and out[0]["compat_short"] and out[1]["compat"] == ""


def test_list_adapters(tmp_path):
    _adapter(tmp_path, "8087", "0026")

    def run(cmd, **kw):
        import subprocess
        return subprocess.CompletedProcess(cmd, 0, stdout="({'Address': <'a0:b1:c2:d3:e4:f5'>, 'Powered': <true>},)")
    assert btcompat.list_adapters(tmp_path, run=run) == [
        {"hci": "hci0", "address": "A0:B1:C2:D3:E4:F5", "chip": "Intel Wi-Fi 6 AX201", "usb_id": "8087:0026"}]
