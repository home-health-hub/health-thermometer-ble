# Project notes for ble-health-thermometer

## What makes this repo different from its siblings

Every other daemon/driver repo in `home-health-hub` targets one
specific manufacturer's device, often with a fully proprietary
protocol (see `etekcity-bp-ble`, or the extensive PT3SBT reverse
engineering in the `home-health-hub/healthhub` project's
`technical/ble-thermometers` research notes). This one is different on
purpose: it targets the public Bluetooth SIG Health Thermometer Profile
generically, because two unrelated vendors (iHealth TS28B, Beurer FT95)
both turned out to implement it rather than a custom protocol. See
`docs/PROTOCOL_NOTES.md` for the full sourcing.

Do not add manufacturer-specific workarounds to `protocol.py` or
`client.py` without strong evidence a real device needs them — the
whole value of this package is staying spec-generic. If a specific
device needs a quirk, prefer isolating it (e.g. an opt-in flag) rather
than changing default behavior for everyone.

## Related repos to watch

- **trividia-truemetrix-ble**:
  https://github.com/home-health-hub/trividia-truemetrix-ble. Not a
  code dependency, but this package's architecture/API shape (Reading/
  DeviceInfo dataclasses, pure protocol.py decoding functions, thin
  client.py wrapper, argparse CLI with short+long flags) was
  deliberately mirrored from it — it's the other standard-BLE-profile
  driver in this org (Bluetooth SIG Glucose Profile) and the closest
  precedent for "confirm against real hardware, then remove the
  warning banner" workflow.

## Protocol verification status

Protocol confirmed standard (not proprietary) by reading two unrelated
vendors' own client code — not by a live capture against real hardware.
See README.md's Protocol notes section and `docs/PROTOCOL_NOTES.md` for
the full sourcing, and `tests/test_protocol.py`'s test vectors, which
are synthetic (hand-derived from the spec's byte layout), not real
captured payloads — unlike `trividia-truemetrix-ble`'s tests.

What is *not* yet verified: this package's own `bleak`-based
`client.py`/`protocol.py` has not been run against any real device
(neither a TS28B nor an FT95 has been acquired/tested). Once tested,
update or remove the README's warning banner, and replace/supplement
the synthetic test vectors with real captured payloads, matching
`trividia-truemetrix-ble`'s convention.

## Open questions for a future session

- Discovery filters by advertised Health Thermometer Service UUID
  (`discover()` in `client.py`). Untested whether either target device
  actually advertises this UUID in scan responses (some BLE stacks only
  expose services after connecting) — if `discover()` comes up empty
  against a real device, connecting by address directly and letting
  `bleak` enumerate services post-connection may be needed instead.
- Whether pairing/bonding is required by either device is unknown.
- The Beurer FT95 third-party reference client uses an empirical
  shortcut decoder instead of a spec-correct IEEE-11073 FLOAT decode
  (see `docs/PROTOCOL_NOTES.md`) — worth understanding *why* once real
  hardware is available, in case it reveals an actual deviation from
  spec in that device's firmware rather than just an implementation
  shortcut by that demo's author.
- iHealth NT13B (a third thermometer in the same product family as
  TS28B) was never checked for standard-vs-proprietary protocol — see
  the `ble-thermometers` research notes in the `healthhub` project.
