# Health Thermometer Profile: Protocol Notes

Working notes on why this package targets the public Bluetooth SIG
Health Thermometer Service (0x1809) generically, rather than one
manufacturer's proprietary protocol.

## Background

Consumer BLE thermometers overwhelmingly use manufacturer-proprietary
protocols gated behind a vendor app (see the iHealth PT3SBT
investigation this package grew out of, in the `home-health-hub`
project's `technical/ble-thermometers` research notes -- not part of
this repo). The question this package answers: are there real, current,
affordable devices that instead speak the open standard, so one driver
can cover more than a single product?

## Confirmed by two independent, unrelated vendors' own client code

Neither confirmation below came from a live capture against real
hardware (that's this package's own open item -- see the README's
warning banner). Both came from directly reading a real client
implementation's source.

### iHealth TS28B

Decompiled from iHealth's own official Android SDK
(`iHealthSDK_2.15.1.jar`, class `TS28BInsSet`). No custom protocol at
all: standard Battery Service (`0000180f-...`), standard Health
Thermometer Service (`00001809-...`) / Temperature Measurement
characteristic (`00002a1c-...`), also references the standard Device
Information Service (`0000180a-...`). The measurement parser is a
field-accurate implementation of the spec: Flags byte (unit/timestamp/
type bits matching the spec exactly), IEEE-11073 32-bit FLOAT value,
optional standard date-time struct, optional standard Temperature Type
enum. The parsing utility class is literally named
`ContinuaDataAnalysis` -- a reference to the Continua/Personal Connected
Health Alliance interoperability guidelines, suggesting this is a
deliberate standards-compliant product line, not a coincidence.

TS28B is online-measurement-only (no offline history storage) and, as
far as could be determined, is not currently in normal retail
circulation -- the only listing found was NOS (new-old-stock) on a
secondhand marketplace.

### Beurer FT95

Found via a small third-party open-source project
([Ben-Burke/web-bluetooth](https://github.com/Ben-Burke/web-bluetooth),
`beurer-ft95.html`) -- a completely different, unrelated manufacturer
(German medical devices, no relation to iHealth/Andon Health). Confirms
the identical standard:

```js
var ThermometerService = '00001809-0000-1000-8000-00805f9b34fb';
var TemperatureCharacteristic = 0x2a1C;
```

Two unrelated vendors independently building to the same open spec is
real corroboration this is a genuine (if under-used) standard in this
device category, not a fluke specific to one product line.

That demo's own measurement-decoding code is informative but **not
something this package copies**: it defines a correct IEEE-11073 FLOAT
decoder (`calculateValue`) but never actually calls it, using instead an
empirical shortcut (`extractFinalFormatValue`: read two bytes, byte-swap,
divide by 10) that isn't the general-purpose spec decode. This package's
`protocol.py` implements the real spec decoder instead (see its own
docstring and `tests/test_protocol.py` for verification against
hand-derived spec-correct byte vectors).

FT95 is, as of this writing, actively and widely sold (Amazon, eBay,
multiple sellers including bulk lots) at roughly $12-13/unit -- by far
the more realistic device to actually test this package against.

## What isn't confirmed yet

- **This package's own implementation has not been run against real
  hardware.** The protocol understanding is well-sourced (two
  independent vendors); `client.py`/`protocol.py` built on top of it
  aren't confirmed working end-to-end. See the README's warning banner.
- Whether other Health Thermometer Profile devices exist beyond these
  two, and whether they're equally standards-compliant, is unknown.
- The reserved-value handling in `decode_ieee11073_float` (NaN,
  +/-INFINITY, NRes) is implemented per spec but has never been observed
  triggered by a real device in this investigation.
- Whether these devices require BLE pairing/bonding, and what their
  advertising/connection lifecycle looks like in practice (e.g. does the
  device advertise continuously, or only briefly after a measurement
  button press) is unconfirmed.
