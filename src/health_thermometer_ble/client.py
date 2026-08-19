"""Bluetooth LE client for standard Health Thermometer Profile devices.

Unlike the other drivers in this project, this package is intentionally
not written against one specific product. It targets the public
Bluetooth SIG Health Thermometer Service (0x1809) generically, so it
should work against any compliant device -- confirmed independently by
two unrelated vendors' own client code (iHealth TS28B, Beurer FT95, see
docs/PROTOCOL_NOTES.md), not against one manufacturer's SDK. Discovery
therefore filters by advertised *service*, not by device name.

These are instant-read thermometers (button press -> one notification),
not history-streaming devices -- there's no multi-record download to
wait out, just a single reading per read_once() call.

Uses the `bleak` package for cross-platform BLE access (BlueZ on Linux,
Core Bluetooth on macOS, WinRT on Windows).
"""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from . import protocol
from .const import (
    BATTERY_LEVEL_UUID,
    DEFAULT_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_READ_TIMEOUT_SECONDS,
    FIRMWARE_REVISION_STRING_UUID,
    HEALTH_THERMOMETER_SERVICE_UUID,
    MANUFACTURER_NAME_STRING_UUID,
    MODEL_NUMBER_STRING_UUID,
    SERIAL_NUMBER_STRING_UUID,
    SOFTWARE_REVISION_STRING_UUID,
    TEMPERATURE_MEASUREMENT_UUID,
)
from .data import DeviceInfo, Reading

_LOGGER = logging.getLogger(__name__)


class ThermometerError(RuntimeError):
    """Raised for thermometer communication failures not covered by a more specific error."""


async def discover(timeout: float = 5.0) -> list[BLEDevice]:
    """Scan for and return BLE devices advertising the Health Thermometer Service.

    Filters by advertised service UUID rather than device name, since
    this package targets any standards-compliant device, not one
    product. Not every OS/adapter combination reliably reports
    service UUIDs in scan responses -- if a known-compliant device
    doesn't show up here, connecting directly by address (skipping
    discover()) may still work.
    """
    found = await BleakScanner.discover(timeout=timeout, return_adv=True)
    matches = []
    for device, advertisement in found.values():
        service_uuids = [uuid.lower() for uuid in advertisement.service_uuids]
        if HEALTH_THERMOMETER_SERVICE_UUID.lower() in service_uuids:
            matches.append(device)
    return matches


async def _read_optional_string(client: BleakClient, uuid: str) -> str | None:
    """Read an optional string characteristic, if the device exposes it.

    Not every device is guaranteed to expose every optional Device
    Information Service characteristic -- absence is a normal outcome,
    not an error worth surfacing to callers.
    """
    try:
        value = await client.read_gatt_char(uuid)
    except BleakError:
        return None
    return value.decode("utf-8", errors="replace").strip() or None


async def _read_optional_battery(client: BleakClient) -> int | None:
    """Read Battery Level (0x2A19), if the device exposes the Battery Service."""
    try:
        value = await client.read_gatt_char(BATTERY_LEVEL_UUID)
    except BleakError:
        return None
    return value[0] if value else None


class ThermometerBleClient:
    """Client for one Health Thermometer Profile device over Bluetooth LE.

    Usage:

        async with ThermometerBleClient(address) as client:
            info = await client.get_device_info()
            reading = await client.read_once()

    `address` is a BLE address (a platform-specific identifier on
    macOS), typically from a `BLEDevice` returned by `discover()`.
    """

    def __init__(
        self,
        address: str,
        *,
        name: str | None = None,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
        read_timeout: float = DEFAULT_READ_TIMEOUT_SECONDS,
    ) -> None:
        self._address = address
        self._name = name
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._client: BleakClient | None = None

    async def __aenter__(self) -> ThermometerBleClient:
        await self.connect()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        if self._client is not None:
            return
        client = BleakClient(self._address, timeout=self._connect_timeout)
        await client.connect()
        self._client = client

    async def disconnect(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.disconnect()
        finally:
            self._client = None

    async def get_device_info(self) -> DeviceInfo:
        """Read device identity from the standard Device Information/Battery Services."""
        if self._client is None:
            raise ThermometerError("Not connected")
        return DeviceInfo(
            manufacturer=await _read_optional_string(self._client, MANUFACTURER_NAME_STRING_UUID),
            model=await _read_optional_string(self._client, MODEL_NUMBER_STRING_UUID),
            serial_number=await _read_optional_string(self._client, SERIAL_NUMBER_STRING_UUID),
            firmware_version=await _read_optional_string(
                self._client, FIRMWARE_REVISION_STRING_UUID
            ),
            software_version=await _read_optional_string(
                self._client, SOFTWARE_REVISION_STRING_UUID
            ),
            battery_percent=await _read_optional_battery(self._client),
            address=self._address,
            name=self._name,
        )

    async def read_once(self) -> Reading:
        """Subscribe to Temperature Measurement and return the first valid reading.

        These devices take a single measurement per button press and
        push exactly one notification -- this waits for that one
        notification (skipping over any reserved-value/error payloads,
        see protocol.decode_ieee11073_float) rather than collecting a
        stream. Raises ThermometerError on timeout.
        """
        if self._client is None:
            raise ThermometerError("Not connected")

        loop = asyncio.get_running_loop()
        result: asyncio.Future[Reading] = loop.create_future()

        def _on_measurement(_handle: int, data: bytearray) -> None:
            if result.done():
                return
            reading = protocol.parse_temperature_measurement(bytes(data))
            if reading is not None:
                result.set_result(reading)

        await self._client.start_notify(TEMPERATURE_MEASUREMENT_UUID, _on_measurement)
        try:
            return await asyncio.wait_for(result, timeout=self._read_timeout)
        except asyncio.TimeoutError as exc:
            raise ThermometerError(
                f"No measurement received within {self._read_timeout}s. "
                "Is the device taking a reading?"
            ) from exc
        finally:
            await self._client.stop_notify(TEMPERATURE_MEASUREMENT_UUID)
