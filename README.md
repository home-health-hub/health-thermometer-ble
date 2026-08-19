# health-thermometer-ble

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white) ![Bluetooth LE](https://img.shields.io/badge/Bluetooth-LE-0082FC?logo=bluetooth&logoColor=white)

[![License: GPL-3.0](https://img.shields.io/badge/license-GPL--3.0-blue)](https://github.com/home-health-hub/health-thermometer-ble/blob/main/LICENSE) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/home-health-hub/health-thermometer-ble#contributing) [![Discussions](https://img.shields.io/badge/discussions-welcome-blue)](https://github.com/home-health-hub/health-thermometer-ble/discussions)

A standalone Python Bluetooth LE client for **standard Health
Thermometer Profile** devices. Unlike this project's other drivers,
this one is intentionally not written against a single product: it
targets the public Bluetooth SIG Health Thermometer Service (`0x1809`)
generically, so it should work against any compliant device, not just
one manufacturer's meter. It reads device identity and a temperature
reading directly from the device over BLE and keeps everything local:
there's no dependency on any manufacturer cloud service or companion
app.

> [!WARNING]
> **Work in progress.** The GATT protocol (Health Thermometer Service,
> Temperature Measurement byte format) is confirmed standard by two
> independent, unrelated vendors' own client code — see [Protocol
> notes](#protocol-notes) — not by a live capture against real
> hardware. This package's own `bleak`-based implementation hasn't been
> run against real hardware yet either. Treat it as
> protocol-correct-on-paper until that's happened. This notice will be
> removed once confirmed.

## Disclaimer

This is an unofficial, independently developed client, built directly
against the public Bluetooth SIG Health Thermometer Profile
specification. The author and contributors are not affiliated with any
device manufacturer. **This is a personal-use tool for reading data
from your own thermometer, not a medical product.** Don't use it to
make treatment decisions. Read your thermometer's own display for that.

## Features

- Discovers Health Thermometer Profile devices over Bluetooth LE by
  advertised **service**, not device name — works with any compliant
  device, not a hardcoded product list.
- Reads device identity from the standard Device Information Service:
  manufacturer, model, serial number, firmware/software version, plus
  battery level from the standard Battery Service.
- Reads a single temperature measurement, decoded from the standard
  Temperature Measurement characteristic (unit, optional timestamp,
  optional temperature-type/body-site all handled per spec).
- Ships a `health-thermometer-ble` CLI for one-off use without writing
  any code.
- Nothing here uploads anywhere. Reads stay local.

## Requirements

- A Bluetooth LE thermometer that implements the standard Health
  Thermometer Service (`0x1809`) — confirmed for iHealth TS28B and
  Beurer FT95, see [Protocol notes](#protocol-notes).
- The [`bleak`](https://pypi.org/project/bleak/) Python package
  (cross-platform BLE: BlueZ on Linux, Core Bluetooth on macOS, WinRT on
  Windows).
- On Linux, non-root BLE scanning/connection access typically needs the
  running user to be in the `bluetooth` group (or an equivalent polkit
  rule), depending on distro.

## Installation

```bash
pip install git+https://github.com/home-health-hub/health-thermometer-ble.git
```

## Library usage

```python
import asyncio
from health_thermometer_ble import ThermometerBleClient, discover

async def main():
    devices = await discover()
    async with ThermometerBleClient(devices[0].address, name=devices[0].name) as client:
        info = await client.get_device_info()
        print(info.manufacturer, info.model, info.battery_percent)

        reading = await client.read_once()
        print(f"{reading.value}°{reading.unit}", reading.measured_at, reading.temperature_type)

asyncio.run(main())
```

## CLI usage

```bash
# Scan for and list nearby devices
health-thermometer-ble --discover

# Print device info and exit
health-thermometer-ble --info

# Take one reading, print as JSON
health-thermometer-ble

# Connect to a specific device address instead of scanning
health-thermometer-ble --address AA:BB:CC:DD:EE:FF
```

Run `health-thermometer-ble --help` for all options.

## Protocol notes

This package targets the standard **Bluetooth SIG Health Thermometer
Profile** (Health Thermometer Service `0x1809`), not a
manufacturer-proprietary protocol. Confirmed independently by two
unrelated vendors' own client implementations — see
[`docs/PROTOCOL_NOTES.md`](docs/PROTOCOL_NOTES.md) for the full
writeup; summary below:

- **Temperature Measurement** (`0x2A1C`, notify): the actual reading —
  Flags byte (unit, timestamp-present, temperature-type-present bits),
  IEEE-11073 32-bit FLOAT value, optional standard date-time struct,
  optional standard Temperature Type enum. See
  [`protocol.py`](src/health_thermometer_ble/protocol.py) for the exact
  byte layout, each field documented at the point it's decoded.
- **Battery Level** (`0x2A19`, read, standard Battery Service `0x180F`):
  read once as part of device info.
- **Device Information Service** (`0x180A`): standard optional string
  characteristics, read once as part of device info.
- These are instant-read thermometers (button press → one
  notification), not history-streaming devices — `read_once()` waits
  for exactly one valid measurement, there's no multi-record download.

### Known quirks / limitations

- IEEE-11073 FLOAT reserved bit patterns (NaN, +/-INFINITY, NRes) are
  decoded per spec (`decode_ieee11073_float` returns `None`), but this
  has never been triggered by a real device — no hardware has been
  tested yet.
- Whether BLE pairing/bonding is required, and what the
  advertising/connection lifecycle looks like in practice, is
  unconfirmed.
- `discover()` filters by advertised service UUID; not every OS/adapter
  combination reliably reports service UUIDs in scan responses. If a
  known-compliant device doesn't show up, connecting directly by
  address may still work.

### Not yet implemented

- Intermediate Temperature (`0x2A1E`) and Measurement Interval
  (`0x2A21`) characteristics, both optional per spec, aren't read.
- Reading Temperature Type (`0x2A1D`) as a separate characteristic
  (rather than inline in the measurement) isn't implemented — only
  needed for devices that expose body-site that way instead.

## Contributing

Contributions are welcome!

- **Bug reports**: [Open an issue](https://github.com/home-health-hub/health-thermometer-ble/issues).
- **Everything else** (questions, feature requests, ideas, general discussion): [Use Discussions](https://github.com/home-health-hub/health-thermometer-ble/discussions).
- Pull requests are welcome for bug fixes or discussed features.

## Acknowledgments

- Protocol implemented directly against the [Bluetooth SIG Health
  Thermometer Service / Health Thermometer Profile
  specifications](https://www.bluetooth.com/specifications/specs/health-thermometer-service-1-0/),
  cross-confirmed against two independent vendors' own client code
  (iHealth's official SDK for TS28B; a third-party open-source client
  for Beurer FT95 — see [`docs/PROTOCOL_NOTES.md`](docs/PROTOCOL_NOTES.md)).
- Code review, implementation, and documentation assisted by [Claude](https://www.anthropic.com/claude).

## License

This project is licensed under the **GNU General Public License v3.0**.

See [LICENSE](LICENSE) for more information.
