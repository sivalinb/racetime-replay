# Data guide

## Device-neutral exported files

Use a 5–15 minute continuous recording and its matching workout. Garmin, COROS, Suunto and Apple Watch are examples of recording devices. This app imports the schemas below; it does not connect to their accounts and does not parse FIT/TCX directly. Convert those exports to the canonical CSV, retaining units and timestamps. Metrics depend on device, external sensors and export content.

Export MP4 H.264 from GoPro, Insta360, iPhone, DJI Osmo or Meta glasses. Reframe 360-degree recordings to conventional forward-facing video first. Proprietary raw 360 formats are unsupported. MOV decoding depends on the installed codec. Limits: 15 minutes and 150 MB.

## Canonical CSV

Required time: `timestamp` in ISO 8601 with timezone, or `elapsed_s` as seconds from workout start. Optional fields:

| Column | Unit / meaning | Missing behavior |
|---|---|---|
| speed_mps | metres/second | Unknown outside tolerance; pace derived only at ≥0.4 m/s |
| heart_rate_bpm | beats/minute | Unknown, never zero-filled |
| cadence_spm | total steps/minute, not strides/minute | Unknown |
| running_power_w | watts from the source device | Unknown; do not compare different vendors as equivalent |
| altitude_m | metres | Recorded elevation; no automatic terrain classification |
| latitude, longitude | decimal degrees | Optional, stays on app host |
| spo2_percent | percentage points, e.g. 98, not 0.98 | Spot signal; maximum matching tolerance 0.5 seconds |
| core_temperature_c | sensor-reported core temperature, °C | Unknown unless source is supplied |
| core_temperature_source | explicit external sensor/export origin | Required for every core-temperature value |

Core temperature is never inferred from HR or mapped from `temperature`, `skin_temperature_c` or ambient temperature. Values outside 20–45 °C are treated as invalid parser input, not clinical classifications. Numerical precision reflects the supplied file and does not imply sensor accuracy.

Timestamp is authoritative when both time fields exist. Rows are sorted and duplicate times keep the first row. Invalid/nonfinite values become unknown. Files should contain one workout, retain missing intervals and distinguish measured values from simulations.

## Personal heart-rate zones

Enter the lower bounds for zones 2–5 from your own watch/training profile, in strictly increasing order. Confirm those values before zones are applied. The prototype uses five bands, with exact boundary values entering the higher zone. It does not calculate maximum HR or infer personal thresholds. The mountain example uses explicitly illustrative boundaries of 120/140/160/180 bpm.

A zone-change event requires the new band to persist for at least five sampled seconds. The initial band is a baseline, not a transition. Missing samples and long gaps break continuity. Events use half-open video intervals: start included, end excluded. Zones describe the supplied configuration; they do not establish terrain difficulty or a physiological cause.

## Apple Health XML and GPX

Health XML is an optional format, not the product's required watch brand. Extract the Health archive yourself and select the XML plus a workout start/end time. Supported records: heart rate (`count/min`/`bpm`), running speed (`m/s`, `km/hr`, `mi/hr`), running power (`W`/`watt`), oxygen saturation (`%`). HealthKit-style oxygen fractions such as 0.98 become 98 percentage points; exports already using points are also accepted. Generic body/skin-temperature records are ignored because they do not establish core-sensor provenance. Cadence and core temperature currently require canonical CSV.

GPX reads timestamped locations, altitude and optional heart-rate/speed extensions. If speed is absent, it derives speed from positions only across gaps ≤10 seconds and records `derived_from_gps`. GPS noise can affect that estimate. Optional Health XML can add supported matching readings to GPX. Availability depends on what was recorded and exported.

## Synchronization contract

`workout_s = video_s + offset_s`. If video starts 30 seconds after the workout, enter +30. A single offset is supported; pause edits and variable drift require separate clips. Verify recognizable events near both ends. File creation time does not establish synchronization.

Each video sample finds the nearest valid measurement independently within the shown tolerance, default two seconds. There is no interpolation over long gaps. SpO₂ matching is capped at 0.5 seconds; the original matching timestamp is retained. Core readings also retain their source and sample time. The player labels an earlier oxygen reading separately and does not display it as current.

## Interpretation

The performance brief compares the first valid HR sample with the first later peak; it does not average a whole run or calculate a fitness score. Missing optional readings stay missing in the comparison. See [performance review](PERFORMANCE_REVIEW.md) for proposed experiments and limitations.

OpenCV optical flow measures apparent displacement on 320 × 180 grayscale frames around 2 Hz, in pixels per interval. It is not running speed. Camera handling, stabilization, texture and light affect it. Separate diagnostic events still identify candidate stops, missing speed, apparent speed/motion conflicts and repeated frames. These checks do not prove a cause.
