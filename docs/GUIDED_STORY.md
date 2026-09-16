# A clearer watch + video demonstration

Open the app with `?story=1&present=1` for the four-step guided story. The full
workspace remains available at the root URL. From the presentation, the live
link adds `start=watch` because its stream-crossing opener has already played.

1. **Why video?** A separate Mixkit clip shows runners crossing water. No watch
   measurements are attached to this opening example.
2. **Read the watch.** An explicitly simulated workout moves from 134 to 154 bpm,
   illustrative Zone 2 to Zone 3, and pace 8:00 to 10:30/km at 0:12.
3. **Reveal the moment.** The Pexels POV clip shows boots stepping across uneven
   rocks. The video player uses the same clock and analysis as the full app.
   The authored visual note is human reviewed; there is no automatic terrain label.
4. **Plan next time.** Review an observation, edit an experiment, explicitly
   confirm the observation, then save and download the plan. The local agent can
   also produce a cited measurement comparison through the evidence expander.

The recorded people are not participants, customers or endorsers. The two clips
are not one outing. Simulated measurements never establish a physiological cause
or validate a performance benefit. Oxygen and temperature are absent in this
fixture; the full workspace retains support for available, sourced signals.
Wildlife, weather recognition and live emergency alerts remain future work.

## Preparing media

```sh
python scripts/prepare_story_demo.py --ffmpeg /path/to/ffmpeg
```

The script downloads the selected stock sources, preserves speed and chronology,
encodes a local 720p copy and writes a provenance manifest with hashes. Media is
gitignored; it is not redistributed as standalone stock through the repository.
The CSV and source manifest document the reproducible fixture.

- [Stream crossing / Mixkit](https://mixkit.co/free-stock-video/couple-running-over-a-stream-44352/)
  is listed under the [Mixkit Stock Video Free License](https://mixkit.co/license/).
- [Rocky POV / K, Pexels](https://www.pexels.com/video/a-hiker-walking-on-the-edge-of-a-cliff-4606798/)
  uses the [Pexels license](https://www.pexels.com/license/).

No raw video, simulated workout or observation is sent to an external service by
the guided route. The existing full workspace retains its optional cloud and
synthetic observability controls.
