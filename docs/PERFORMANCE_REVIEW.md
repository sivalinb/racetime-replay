# From readings to an improvement worth testing

RaceTime Replay is brand-neutral. Garmin, COROS, Suunto and Apple Watch are examples of devices that can record a workout. The prototype accepts compatible exported files, not direct account connections. The supported schema determines which readings are available; a logo does not imply that every watch exports every metric.

## The user journey

1. Load a video and a matching workout export. Confirm their time offset and your own zone boundaries.
2. Replay effort: jump to a sustained heart-rate zone change or the recorded HR peak. Compare the visible scene with pace, cadence, elevation and power when recorded.
3. Ask Replay: get a cited, reproducible comparison. The numbers come from Python, not an LLM estimate.
4. Review and improve: distinguish observed changes from possible explanations. Select a proposed experiment, describe what is actually visible, and explicitly save a reviewed observation.
5. On another comparable session, test the proposal and compare results. The current prototype exports the evidence; automated multi-run evaluation remains future work.

## What the result means

`replay/performance.py` compares the first valid HR sample with the first later peak in the selected clip. It reports readings at those two instants, not whole-run averages or a fitness score. The selection is not a controlled experiment: starting HR, sensor lag, alignment error, route and conditions can all affect interpretation. If the first sample is already the maximum or there is too little HR data, it declines to manufacture a rising-effort comparison.

A higher HR with higher recorded power/elevation and slower pace is an observed co-occurrence. It is not proof that the terrain, temperature, oxygen level or fatigue caused the change. The viewer inspects the scene; OpenCV does not currently label climbs or technique.

The suggested next step is a template for human review: compare a steadier-effort attempt on a similar segment using the athlete's own training plan. Record segment time, time in the intended zone, perceived effort and video context. Similar time with fewer departures from intended effort is a candidate improvement to verify across repeated sessions. No personalized HR, temperature, hydration or heat-exposure targets are prescribed.

## Optional temperature and oxygen

Core temperature requires an explicit `core_temperature_c` column and a nonempty `core_temperature_source`. Generic temperature, skin temperature and ambient temperature are never substituted. A compatible external sensor may report an estimate of core temperature; this is sensor-reported data, not a measurement inferred from video or heart rate. Export capabilities vary. [COROS CORE support](https://support.coros.com/hc/en-us/articles/4416368334868-CORE-Body-Temperature-Sensor) and [CORE FIT field documentation](https://help.corebodytemp.com/hc/en-us/articles/35577787408914-FIT-Files) describe sensor/device compatibility. Convert exported fields to the canonical CSV before import; native FIT parsing is not implemented.

SpO₂ is optional and can be intermittent. A spot reading at the start is not a current reading later in the video. The UI displays the old reading separately with its timestamp and leaves the current value missing. Movement affects wrist blood-oxygen measurement; availability depends on device and region. [Apple measurement guidance](https://support.apple.com/en-au/120358), [Garmin Pulse Ox](https://www.garmin.com/en-AU/garmin-technology/health-science/pulse-ox/).

Neither signal establishes a medical cause, safety to continue, heat strain or oxygen-limited performance. This prototype is a post-activity review tool.

## Evaluation scope

`tests/test_performance.py` checks zone boundaries, sustained transitions, gaps, XML units, core provenance, missing oxygen, consistent synthetic exports, cited results and insufficient-evidence behavior. These tests verify code behavior. They do not validate physiological accuracy or performance benefits. A paired real-run pilot, independent labels and repeated sessions are still required.
