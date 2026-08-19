"""Pure decoding functions for the standard Bluetooth Health Thermometer Profile.

No I/O here -- everything in this module is a pure function over raw
bytes, decoding the standard Temperature Measurement (0x2A1C)
characteristic per the Bluetooth SIG Health Thermometer Profile spec
(IEEE 11073-20601 32-bit FLOAT encoding for the temperature value,
org.bluetooth.characteristic.date_time for the optional timestamp).

Confirmed independently by two unrelated vendors' own client code (see
docs/PROTOCOL_NOTES.md) to speak this standard format rather than a
proprietary one -- not yet confirmed against real hardware by this
package's own implementation.
"""

from __future__ import annotations

import datetime

from .const import (
    FLAG_TEMPERATURE_TYPE_PRESENT,
    FLAG_TIMESTAMP_PRESENT,
    FLAG_UNIT_FAHRENHEIT,
    TEMPERATURE_TYPES,
)
from .data import Reading

#: Reserved 24-bit mantissa bit patterns for the IEEE 11073-20601 FLOAT
#: type, checked against the raw unsigned mantissa before sign
#: conversion. A device reports one of these to signal a measurement
#: error rather than a real value (e.g. "no valid reading yet").
_RESERVED_MANTISSA_POSITIVE_INFINITY = 0x7FFFFF
_RESERVED_MANTISSA_NAN = 0x800000
_RESERVED_MANTISSA_NRES = 0x800001
_RESERVED_MANTISSA_NEGATIVE_INFINITY = 0x800002
_RESERVED_MANTISSAS = {
    _RESERVED_MANTISSA_POSITIVE_INFINITY,
    _RESERVED_MANTISSA_NAN,
    _RESERVED_MANTISSA_NRES,
    _RESERVED_MANTISSA_NEGATIVE_INFINITY,
}


def decode_ieee11073_float(raw: bytes) -> float | None:
    """Decode a 4-byte little-endian IEEE 11073-20601 32-bit FLOAT.

    An 8-bit signed exponent (the top byte) and a 24-bit signed mantissa
    (the bottom three bytes), both two's complement:
    value = mantissa * 10**exponent.

    Returns None for the format's reserved special values (NaN,
    +/-INFINITY, NRes) rather than a nonsensical number -- these signal
    "no valid measurement," not a real reading of zero or similar.
    """
    raw_int = int.from_bytes(raw, "little")
    mantissa = raw_int & 0xFFFFFF
    exponent = (raw_int >> 24) & 0xFF

    if mantissa in _RESERVED_MANTISSAS:
        return None

    if exponent >= 0x80:
        exponent -= 0x100
    if mantissa >= 0x800000:
        mantissa -= 0x1000000

    return mantissa * (10**exponent)


def parse_temperature_measurement(raw: bytes) -> Reading | None:
    """Decode a Temperature Measurement (0x2A1C) notification payload.

    Returns None if the value field is one of the format's reserved
    special values (see decode_ieee11073_float) -- a measurement error
    signaled by the device, not a usable reading.
    """
    flags = raw[0]
    unit = "F" if flags & FLAG_UNIT_FAHRENHEIT else "C"

    value = decode_ieee11073_float(raw[1:5])
    if value is None:
        return None

    offset = 5
    measured_at = None
    if flags & FLAG_TIMESTAMP_PRESENT:
        # org.bluetooth.characteristic.date_time: Year (uint16), Month,
        # Day, Hours, Minutes, Seconds (uint8 each) -- 7 bytes. The spec
        # allows an all-zero field to mean "unknown"; not special-cased
        # here since neither confirmed source device has been observed
        # to send it.
        year = int.from_bytes(raw[offset:offset + 2], "little")
        month, day, hour, minute, second = raw[offset + 2:offset + 7]
        measured_at = datetime.datetime(year, month, day, hour, minute, second)
        offset += 7

    temperature_type = None
    if flags & FLAG_TEMPERATURE_TYPE_PRESENT:
        type_code = raw[offset]
        temperature_type = TEMPERATURE_TYPES.get(type_code, str(type_code))
        offset += 1

    return Reading(
        value=value,
        unit=unit,
        measured_at=measured_at,
        temperature_type=temperature_type,
        raw=bytes(raw),
    )
