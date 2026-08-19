"""Data types for the standard Bluetooth Health Thermometer Profile."""

from __future__ import annotations

import dataclasses
import datetime


@dataclasses.dataclass
class Reading:
    """A single decoded Temperature Measurement record.

    Attributes:
        value: Temperature value, in the unit given by `unit`. Decoded
            from the characteristic's IEEE-11073 32-bit FLOAT encoding,
            not converted to a fixed unit -- callers that want a
            specific unit should check `unit` and convert themselves.
        unit: "C" (Celsius) or "F" (Fahrenheit), per the measurement's
            own Flags byte -- not assumed or configured by this package.
        measured_at: Timestamp from the record's optional embedded
            date-time field, or None if the device didn't include one
            (legal per the spec -- not every device/reading has a
            timestamp). Not timezone-aware.
        temperature_type: Decoded Temperature Type field (e.g.
            "Ear (usually ear lobe)"), if the device included one inline
            with the measurement. None if absent -- some devices only
            expose it via a separate read, which this package doesn't
            perform automatically.
        raw: The undecoded Temperature Measurement notification bytes
            this reading was parsed from.
    """

    value: float
    unit: str
    measured_at: datetime.datetime | None
    temperature_type: str | None
    raw: bytes


@dataclasses.dataclass
class DeviceInfo:
    """Device identity, from the standard Device Information Service (0x180A).

    Attributes:
        manufacturer: Manufacturer Name String (0x2A29), if the device
            exposes it.
        model: Model Number String (0x2A24), if the device exposes it.
        serial_number: Serial Number String (0x2A25), if the device
            exposes it.
        firmware_version: Firmware Revision String (0x2A26), if the
            device exposes it.
        software_version: Software Revision String (0x2A28), if the
            device exposes it.
        battery_percent: Battery Level (0x2A19) from the standard
            Battery Service, if the device exposes it.
        address: BLE address (or platform-specific identifier) the
            device was connected at.
        name: Advertised BLE device name.
    """

    manufacturer: str | None
    model: str | None
    serial_number: str | None
    firmware_version: str | None
    software_version: str | None
    battery_percent: int | None
    address: str
    name: str | None
