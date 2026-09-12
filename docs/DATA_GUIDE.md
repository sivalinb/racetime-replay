# Data guide

## Begin with exported files

Use one 10–15 minute recording and its matching workout. Export ordinary MP4 H.264 from GoPro, Insta360, iPhone or Meta glasses. Reframe 360-degree recordings to a conventional forward-facing video first. Proprietary raw 360 formats are not supported. A MOV file works only when this machine's decoder supports its codec. The app does not connect directly to camera or watch accounts.

The bundled demo is a 90-second generated texture animation with invented measurements. It deliberately includes a stop, camera motion while GPS reports zero speed, frozen frames and a speed gap. It is not a visual terrain benchmark.

## Canonical CSV

Required time: `timestamp` in ISO 8601 with timezone, or `elapsed_s` as seconds from workout start. Optional columns:

| Column | Unit | Missing-data behavior |
|---|---|---|
| speed_mps | meters per second | Blank remains unknown outside join tolerance |
| heart_rate_bpm | beats per minute | Blank remains unknown |
| latitude and longitude | decimal degrees | Route is omitted when absent |
| altitude_m | meters | No climb claim without supporting data |

If both time fields exist, timestamp is authoritative. Records are sorted and duplicate timestamps are collapsed to the first row. Out-of-range speed and heart-rate values become unknown, never zero. Uploaded CSV sources should already represent one workout.

## Apple Health and GPX

In Apple Health, open your profile and choose Export All Health Data. Extract the archive yourself and select `export.xml`; the app does not unzip archives. Select an explicit workout start and end time before importing XML. Current supported records are heart rate and running speed, with unit conversion for m/s, km/hr and mi/hr. Other Health records are ignored.

A GPX workout route supplies timestamped locations, altitude, and optional heart-rate extensions. When speed is absent, speed is derived from positions only across gaps of ten seconds or less and labeled `derived_from_gps`. This estimate is sensitive to GPS noise. Upload the optional Health XML beside a GPX file to add matching recorded heart-rate/speed measurements. Availability depends on what was actually recorded and exported.

Sources: [Apple Health export](https://support.apple.com/guide/iphone/share-your-health-data-iph5ede58c3d/26/ios/26), [HealthKit route access](https://developer.apple.com/documentation/healthkit/reading-route-data).

## Synchronization contract

`workout_s = video_s + offset_s`. If video starts 30 seconds after the workout, set +30. A negative offset means video started first. A single offset is supported; pause edits and variable drift require splitting into separate recordings. Verify one recognizable event near the start and another near the end. A filename creation time is not proof of synchronization.

Each video sample independently finds the closest valid workout measurement within tolerance. No interpolation spans long gaps. Heart rate and speed have separate sampling schedules. The default tolerance is two seconds and is shown in the UI. Missing intervals appear in the report. Video time uses decoder timestamps, with nominal FPS as a fallback; variable-frame-rate recordings require field validation.

## Measurement limits

Optical flow is median apparent displacement on 320 by 180 grayscale frames sampled around 2 Hz. It is in pixels per sampled interval, not m/s. Stabilization, camera handling, low texture and lighting changes affect it. A repeated-frame flag cannot distinguish a frozen recorder from a perfectly still scene. Candidate stop detection requires both low visual motion and near-zero recorded speed. Thresholds are experimental and configurable in Python; calibrate with labeled recordings before relying on results.

The route display is a local shape illustration, not a navigation map. It deliberately avoids transmitting coordinates to an external map service.
