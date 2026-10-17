# Class B Only Ports

## Overview
**Status:** deferred (2026-10-17). Cells that only contain **Class B** traffic are ignored and can not become a port or anchorage in the **DDPI**.

Class B transponders are mostly used by fishing boats, leisure craft and small workboats. They send position and static data (ship type, dimensions), but never the `Navigation Status`, `Destination` or `Draught` fields. The planned Class B support uses these vessels only for movement based port events (`no_sog_event`, `no_movement_event`, `drifting_event`, `no_rate_of_turn_event`, `towing_event`). The navigation status, destination and draught events are `null` for Class B, so the `port_score` and `anchorage_score` of a cell are calculated from Class A vessels only.

As a result, a cell without any Class A vessel has no `port_score` or `anchorage_score` and is removed before the port cluster generation.

---

## Benefits of including Class B only cells
- **Small harbours**: marinas, small fishing harbours and island landing sites that are never visited by commercial vessels.
- **Coverage**: better coverage in regions with little Class A traffic.

## Risks
- **Fishing gear beacons**: nets and longlines are often marked with AIS buoys. They stay at the same position for days and look like a perfect `no_movement_event` in open water.
- **Leisure anchoring**: bays, mooring fields and beaches with anchored leisure boats easily pass the minimum days and minimum vessel thresholds of the [event validation](../src/port_event_processing/event_validation.py).
- **No port or anchorage classification**: without the navigation status the current scores can not distinguish between ports and anchorages.
- **Data quality**: Class B reports less often and with less accurate positions, which makes the event statistics noisier.

---

## Requirements
If Class B only ports are added later, they should be a separate port type and not be mixed into the existing scores:

### 1. **MMSI Filter**:
Remove fishing gear beacons and other non-ship MMSIs (e.g. MMSIs starting with `98` or `99`).

### 2. **Vessel Threshold**:
Use a higher minimum number of unique vessels than for Class A cells.

### 3. **Classification**:
Define a port and anchorage rule that does not rely on the navigation status, e.g. based on the `no_movement_event` rate or the distance to the shore.

### 4. **Output Flag**:
Mark these ports in the DDPI export (e.g. `is_small_craft`), so they can be filtered out.

---

## Decision
The DDPI focuses on commercial ports and anchorages for now. This should be revisited once the raw data profiling shows how much Class B traffic remains after the simplification.
