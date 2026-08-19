#!/usr/bin/env python3
"""Standalone command-line client for standard Health Thermometer Profile devices."""

from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import logging
import sys

from ._version import __version__
from .client import ThermometerBleClient, ThermometerError, discover
from .const import DEFAULT_READ_TIMEOUT_SECONDS

_LOGGER = logging.getLogger("ble_health_thermometer")


def _print_json(obj) -> None:
    data = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else obj
    print(json.dumps(data, indent=2, default=str))


async def _run_discover(scan_timeout: float) -> None:
    devices = await discover(timeout=scan_timeout)
    if not devices:
        print("No Health Thermometer Profile devices found.", file=sys.stderr)
        return
    for device in devices:
        print(f"{device.address}  {device.name}")


async def _run(args: argparse.Namespace) -> None:
    address = args.address
    name = None
    if address is None:
        devices = await discover(timeout=args.scan_timeout)
        if not devices:
            raise ThermometerError(
                "No Health Thermometer Profile device found. Is it powered on and advertising?"
            )
        address, name = devices[0].address, devices[0].name

    async with ThermometerBleClient(address, name=name, read_timeout=args.timeout) as client:
        if args.info:
            info = await client.get_device_info()
            _print_json(info)
            return

        reading = await client.read_once()
        _print_json(reading)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-d", "--discover", action="store_true", help="scan for devices, list them, and exit"
    )
    parser.add_argument(
        "-a", "--address", help="BLE address to use (from --discover); default: first found"
    )
    parser.add_argument(
        "-i", "--info", action="store_true",
        help="print device info (manufacturer/model/serial/firmware/battery) and exit",
    )
    parser.add_argument(
        "-t", "--timeout", type=float, default=DEFAULT_READ_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help=f"how long to wait for a measurement notification "
             f"(default: {DEFAULT_READ_TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "-s", "--scan-timeout", type=float, default=5.0, metavar="SECONDS",
        help="BLE scan duration when discovering a device (default: 5.0)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ble-health-thermometer console script."""
    args = _parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        if args.discover:
            asyncio.run(_run_discover(args.scan_timeout))
            return
        asyncio.run(_run(args))
    except ThermometerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
