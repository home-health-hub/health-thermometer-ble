"""Constants for the standard Bluetooth SIG Health Thermometer Profile.

This package targets the public Health Thermometer Service (0x1809) and
Temperature Measurement characteristic (0x2A1C) -- not a manufacturer-
proprietary protocol. Confirmed independently by two unrelated vendors'
own client implementations: iHealth's official Android SDK (device
TS28B) and a third-party reverse-engineered client for a Beurer FT95.
See docs/PROTOCOL_NOTES.md for both sources. Neither has been confirmed
against real hardware from this package's own client.py yet.
"""

from __future__ import annotations

# Health Thermometer Service (0x1809) and its characteristics.
HEALTH_THERMOMETER_SERVICE_UUID = "00001809-0000-1000-8000-00805f9b34fb"
TEMPERATURE_MEASUREMENT_UUID = "00002a1c-0000-1000-8000-00805f9b34fb"
TEMPERATURE_TYPE_UUID = "00002a1d-0000-1000-8000-00805f9b34fb"
INTERMEDIATE_TEMPERATURE_UUID = "00002a1e-0000-1000-8000-00805f9b34fb"
MEASUREMENT_INTERVAL_UUID = "00002a21-0000-1000-8000-00805f9b34fb"

# Battery Service (0x180F) and its characteristic.
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# Device Information Service (0x180A) and its characteristics.
DEVICE_INFORMATION_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_STRING_UUID = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_STRING_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_STRING_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_STRING_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
SOFTWARE_REVISION_STRING_UUID = "00002a28-0000-1000-8000-00805f9b34fb"

#: Temperature Measurement flags (byte 0), per the Bluetooth SIG Health
#: Thermometer Profile spec.
FLAG_UNIT_FAHRENHEIT = 0x01  # 0 = Celsius, 1 = Fahrenheit
FLAG_TIMESTAMP_PRESENT = 0x02
FLAG_TEMPERATURE_TYPE_PRESENT = 0x04

#: Temperature Type field (org.bluetooth.characteristic.temperature_type),
#: per the Bluetooth SIG assigned numbers. Sent either inline in the
#: measurement (if FLAG_TEMPERATURE_TYPE_PRESENT is set) or read
#: separately from TEMPERATURE_TYPE_UUID.
TEMPERATURE_TYPES = {
    1: "Armpit",
    2: "Body (general)",
    3: "Ear (usually ear lobe)",
    4: "Finger",
    5: "Gastro-intestinal Tract",
    6: "Mouth",
    7: "Rectum",
    8: "Toe",
    9: "Tympanum (ear drum)",
}

#: How long to wait for a single measurement notification before giving
#: up. These are instant-read thermometers (button press -> one
#: notification), not history-streaming devices like a glucose meter --
#: there's no multi-record download to wait out.
DEFAULT_READ_TIMEOUT_SECONDS = 15.0

#: How long to wait for a BLE connection before giving up.
DEFAULT_CONNECT_TIMEOUT_SECONDS = 15.0
