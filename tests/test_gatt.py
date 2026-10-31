from tretlager.bridge import gatt
from tretlager.bridge.config import BASE_PORT, BridgeConfig


def test_heart_rate_uint8_and_uint16():
    assert gatt.decode_heart_rate(bytes([0x00, 72])) == {"heart_rate": 72}
    assert gatt.decode_heart_rate(bytes([0x01, 0x2C, 0x01])) == {"heart_rate": 300}


def test_indoor_bike_data_speed_cadence_power():
    # Flags 0x0044: speed (bit 0 = 0), cadence (bit 2), power (bit 6)
    data = bytes([0x44, 0x00, 0xC4, 0x09, 0xB4, 0x00, 0xD2, 0x00])
    assert gatt.decode_indoor_bike_data(data) == {"speed_kmh": 25.0, "cadence": 90.0, "power": 210}


def test_indoor_bike_data_skips_optional_fields():
    # Flags 0x0274: speed, cadence, distance (3 B), resistance (2 B), power, heart rate
    data = bytes([0x74, 0x02, 0x10, 0x27, 0xA0, 0x00, 1, 2, 3, 5, 0, 0x2C, 0x01, 140])
    assert gatt.decode_indoor_bike_data(data) == {"speed_kmh": 100.0, "cadence": 80.0, "power": 300,
                                                  "heart_rate": 140}


def test_cycling_power():
    assert gatt.decode_cycling_power(bytes([0x00, 0x00, 0xFA, 0x00])) == {"power": 250}


def test_role_detection():
    assert gatt.role_for([gatt.CYCLING_POWER, gatt.FTMS]) == "trainer"
    assert gatt.role_for([gatt.HEART_RATE]) == "heartrate"
    assert gatt.role_for([]) == "other"


def test_config_ports_and_roundtrip(tmp_path):
    cfg = BridgeConfig()
    a = cfg.add("ce:e7:78:71:fe:2e", "Wahoo KICKR C058", "trainer")
    b = cfg.add("E4:53:90:56:BB:73", "HRMPro+", "heartrate")
    assert (a.port, b.port) == (BASE_PORT, BASE_PORT + 1)
    assert cfg.add("CE:E7:78:71:FE:2E", "x", "trainer") is a  # no duplicate
    cfg.remove(a.address)
    assert cfg.add("11:22:33:44:55:66", "new", "power").port == BASE_PORT  # a free port is used
    path = tmp_path / "bridge.json"
    cfg.save(path)
    again = BridgeConfig.load(path)
    assert [d.address for d in again.devices] == ["E4:53:90:56:BB:73", "11:22:33:44:55:66"]
