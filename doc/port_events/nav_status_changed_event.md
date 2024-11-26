# Nav Status Code Changed Event

# NavStatusChangedEvent

## Overview

The **NavStatusChangedEvent** represents a specific type of event in the DDPI port events system, triggered when a ship's navigation status (`Nav Status`) field in AIS data changes. This event provides critical insights into vessel activity, particularly in and around ports, as it tracks changes in the operational state of ships (e.g., moving, anchored, or moored).

---

## Purpose

Monitoring changes in the `Nav Status` field is essential for:
- **Port Operations Analysis**: Detecting when ships switch from being underway to anchored, moored, or otherwise stationary, which often indicates arrival or docking.
- **Behavioral Insights**: Identifying patterns in ship activities and movements based on navigation status changes.
- **Port Clustering and Validation**: Assisting in defining and validating port boundaries by correlating navigation status changes with geospatial data.

---

## Event Definition

A `NavStatusChangedEvent` is triggered when:
1. A ship's `Nav Status` field changes in consecutive AIS messages.
2. The change occurs within a defined area of interest (e.g., near or inside port boundaries).

Key attributes of the event include:
- **Previous Navigation Status**: The ship's status before the change.
- **New Navigation Status**: The updated navigation status.
- **Timestamp**: The time when the status change was detected.
- **Ship Information**:
  - MMSI (Maritime Mobile Service Identity)
  - IMO (International Maritime Organization) number (if available)
  - Vessel name (if available)
- **Geographical Location**:
  - Latitude and longitude of the ship at the time of the event.
  - Closest identified port (if applicable).

---

## Navigation Status Codes

The AIS `Nav Status` field uses integer codes to represent different navigation states. Examples include:
- **0**: Underway using engine
- **1**: At anchor
- **2**: Not under command
- **3**: Restricted maneuverability
- **4**: Constrained by her draught
- **5**: Moored
- **6**: Aground

---

## Use Cases

1. **Port Arrival Detection**  
   When a ship changes its status from "Underway" (`0`) to "Moored" (`5`) or "At Anchor" (`1`), this event can indicate the arrival at a port or anchorage.

2. **Operational State Changes**  
   Capturing transitions such as "At Anchor" to "Underway" to monitor departures or movements within port boundaries.

3. **Port Event Validation**  
   Correlating navigation status changes with other port events, such as `DestinationChangedEvent`, to improve the accuracy of port activity detection.

---

## Example

Here is an example of a `NavStatusChangedEvent` in JSON format:

```json
{
  "event_type": "NavStatusChangedEvent",
  "timestamp": "2024-11-25T14:30:00Z",
  "ship": {
    "mmsi": "123456789",
    "imo": "9876543",
    "name": "Vessel Name"
  },
  "location": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "nearest_port": "San Francisco"
  },
  "previous_nav_status": 0,
  "new_nav_status": 5
}


![ais heatmap](../../static/images/nav_status.png)