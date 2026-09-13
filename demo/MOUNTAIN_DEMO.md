# Mountain trail POV demo

This example replaces the abstract motion pattern in the default app view with
real first-person hiking footage of the trail ahead. It is not footage of the
user, a verified running workout, or a source of physiological measurements.

## Paired inputs

- `mountain-pov.mp4`: approximately 60 seconds, 1280 × 720, H.264, 24 fps.
- `mountain-workout.csv`: 60 simulated one-second samples with speed, heart rate,
  altitude, and a fictional route. Video time zero aligns with workout time zero.
- `mountain-health.xml`: Apple Health-shaped speed and heart-rate records with
  exactly the same timestamps and values as the CSV; no real Apple Watch export.
- `mountain-provenance.json`: source, license, processing and scenario details.

The source is **Point of View of a Person Hiking a Rocky Hill**, by **I Am Sorin**:
https://www.pexels.com/video/point-of-view-of-a-person-hiking-a-rocky-hill-6798218/

License: https://www.pexels.com/license/

The source is downscaled and encoded for browser playback. There are no inserted
freezes, loops, generated scenes, or playback-speed changes. The creator does not
endorse this application. The MP4 is an application demo asset, not licensed under
any repository code license; its use remains subject to the Pexels license.

## What to show

1. Select **Explore demo → Mountain trail POV** and play the synchronized video.
2. At 20–27 seconds, the mock watch reports zero speed while the real camera keeps
   moving. The application flags a source disagreement, not a confirmed stop.
3. Speed values are deliberately absent at seconds 43–50 inclusive. With the
   default two-second nearest-sample tolerance, the detected missing interval is
   44.5–49 seconds. Heart rate remains available.
4. Ask **Why do the video and watch speed disagree?** Review the timestamped
   evidence and its uncertainty. The app does not infer terrain or medical causes.
5. Select **Diagnostic motion fixture** only to demonstrate deliberately injected
   stop and repeated-frame cases. Its existing evaluation reports remain unchanged.

These are constructed demonstration cases, not field validation. A shared time
axis does not turn simulated signals into measurements of the person filming.

## Reproduce the simulated workout

```bash
python scripts/make_mountain_workout.py
```

For XML upload, the simulated range is `2026-08-01T07:00:00+00:00` through
`2026-08-01T07:00:59+00:00`. CSV includes the fictional route; XML includes only
the supported speed and heart-rate quantity records.
