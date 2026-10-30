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


def test_hrm_pro_on_ax201_warns():
    ax201 = btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")
    for name in ("HRMPro+:462237", "HRM-Pro:123456"):
        text = btcompat.issue_for(ax201, name)
        assert "Garmin HRM-Pro" in text and "AX201" in text
    assert btcompat.issue_for(ax201, "TICKR 9029") == ""


def test_hrm_pro_on_other_chip_is_fine():
    assert btcompat.issue_for(btcompat.Chip("8087:0029", "Intel Wi-Fi 6 AX200"), "HRMPro+:462237") == ""
    assert btcompat.issue_for(None, "HRMPro+:462237") == ""


def test_annotate_adds_field():
    ax201 = btcompat.Chip("8087:0026", "Intel Wi-Fi 6 AX201")
    out = btcompat.annotate([{"name": "HRMPro+:1"}, {"name": "Wahoo KICKR C058"}], ax201)
    assert out[0]["compat"] and out[1]["compat"] == ""
