# Bundled asset provenance

This directory contains reproducible application inputs and evaluation fixtures.
The hiking footage is not a verified running workout or a source of physiological
measurements. All accompanying watch values are simulated.

## Paired inputs

- `mountain-pov.mp4`: approximately 60 seconds, 1280 × 720, H.264, 24 fps.
- `mountain-workout.csv`: 60 simulated one-second samples with speed, heart rate,
  cadence, power, a single SpO₂ spot sample, explicit simulated external core-sensor readings, altitude, and a fictional route. Video time zero aligns with workout time zero.
- `mountain-health.xml`: Apple Health-shaped speed, heart-rate, power and oxygen records with
  exactly the same timestamps and values as the CSV; no real sports-watch export.
- `mountain-provenance.json`: source, license, processing and scenario details.

The source is **Point of View of a Person Hiking a Rocky Hill**, by **I Am Sorin**:
https://www.pexels.com/video/point-of-view-of-a-person-hiking-a-rocky-hill-6798218/

License: https://www.pexels.com/license/

The source is downscaled and encoded for browser playback. There are no inserted
freezes, loops, generated scenes, or playback-speed changes. The creator does not
endorse this application. The MP4 is an application asset, not licensed under
any repository code license; its use remains subject to the Pexels license.

## Evaluation boundaries

The generated motion fixture, workout CSV and ground-truth JSON support controlled
regression tests. The mountain input has a separate provenance record and is not
an independent field benchmark. A shared time axis does not turn simulated
signals into measurements of the person filming.

## Reproduce the simulated workout

```bash
python scripts/make_mountain_workout.py
```

For XML upload, the simulated range is `2026-08-01T07:00:00+00:00` through
`2026-08-01T07:00:59+00:00`. CSV includes the fictional route; XML includes only
the supported speed, heart-rate, power and oxygen records. Cadence, core temperature and route fields are CSV-only. The core readings span 37.80–37.90 °C and do not imply heat strain. Heart rate rises 134 → 168 bpm with illustrative Zone 2 → Zone 4 thresholds; speed remains positive.
