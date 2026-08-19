from __future__ import annotations

import datetime

import pytest

from ble_health_thermometer.protocol import (
    decode_ieee11073_float,
    parse_temperature_measurement,
)

# Synthetic test vectors, derived directly from the Bluetooth SIG Health
# Thermometer Profile spec's byte layout -- NOT captured from real
# hardware (unlike this project's sibling packages, no device has
# confirmed this package's own implementation yet; see README's warning
# banner and docs/PROTOCOL_NOTES.md).

# 37.0C: mantissa=370 (0x000172), exponent=-1 (0xFF), little-endian.
_VALUE_37_0C = bytes([0x72, 0x01, 0x00, 0xFF])

# 98.6F: mantissa=986 (0x0003DA), exponent=-1 (0xFF), little-endian.
_VALUE_98_6F = bytes([0xDA, 0x03, 0x00, 0xFF])

# 2026-08-19 10:30:00: Year=2026 (0x07EA LE), Month=8, Day=19(0x13),
# Hours=10, Minutes=30(0x1E), Seconds=0. Per
# org.bluetooth.characteristic.date_time.
_TIMESTAMP_2026_08_19_10_30_00 = bytes([0xEA, 0x07, 0x08, 0x13, 0x0A, 0x1E, 0x00])

# Temperature Type: 4 = Finger, per the Bluetooth SIG assigned numbers.
_TYPE_FINGER = bytes([0x04])


def test_decode_ieee11073_float_37_0c():
    assert decode_ieee11073_float(_VALUE_37_0C) == 37.0


def test_decode_ieee11073_float_negative_value():
    # -10.0: mantissa=-10 (0xFFFFF6 in 24-bit two's complement), exponent=0.
    raw = bytes([0xF6, 0xFF, 0xFF, 0x00])
    assert decode_ieee11073_float(raw) == -10.0


def test_decode_ieee11073_float_reserved_values_return_none():
    for mantissa in (0x7FFFFF, 0x800000, 0x800001, 0x800002):  # +INF, NaN, NRes, -INF
        raw = mantissa.to_bytes(3, "little") + bytes([0x00])
        assert decode_ieee11073_float(raw) is None


def test_parse_temperature_measurement_minimal_celsius():
    raw = bytes([0x00]) + _VALUE_37_0C  # Flags: no timestamp, no type
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    assert reading.value == 37.0
    assert reading.unit == "C"
    assert reading.measured_at is None
    assert reading.temperature_type is None
    assert reading.raw == raw


def test_parse_temperature_measurement_fahrenheit_flag():
    raw = bytes([0x01]) + _VALUE_98_6F  # Flags: unit=Fahrenheit
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    # mantissa * 10**exponent is a float computation -- exact for 37.0
    # above but not guaranteed for every value (986 * 0.1 != 98.6 to the
    # last bit), same as any IEEE 754 double. approx, not a decoder bug.
    assert reading.value == pytest.approx(98.6)
    assert reading.unit == "F"


def test_parse_temperature_measurement_with_timestamp():
    raw = bytes([0x02]) + _VALUE_37_0C + _TIMESTAMP_2026_08_19_10_30_00
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    assert reading.measured_at == datetime.datetime(2026, 8, 19, 10, 30, 0)
    assert reading.temperature_type is None


def test_parse_temperature_measurement_with_temperature_type():
    raw = bytes([0x04]) + _VALUE_37_0C + _TYPE_FINGER
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    assert reading.measured_at is None
    assert reading.temperature_type == "Finger"


def test_parse_temperature_measurement_with_timestamp_and_type():
    raw = bytes([0x06]) + _VALUE_37_0C + _TIMESTAMP_2026_08_19_10_30_00 + _TYPE_FINGER
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    assert reading.measured_at == datetime.datetime(2026, 8, 19, 10, 30, 0)
    assert reading.temperature_type == "Finger"


def test_parse_temperature_measurement_unknown_type_code_falls_back_to_raw_number():
    raw = bytes([0x04]) + _VALUE_37_0C + bytes([99])  # 99 isn't a defined Temperature Type
    reading = parse_temperature_measurement(raw)

    assert reading is not None
    assert reading.temperature_type == "99"


def test_parse_temperature_measurement_returns_none_for_reserved_value():
    nan_value = (0x800000).to_bytes(3, "little") + bytes([0x00])
    raw = bytes([0x00]) + nan_value
    assert parse_temperature_measurement(raw) is None
