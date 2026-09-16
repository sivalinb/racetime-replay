# Future visual understanding and optimization

## Next evidence layer

Add a vision model that proposes timestamped observations such as a turn, stairs, a queue or a change in surface. OpenCV continues to handle decoding, frame selection and motion; the learned model supplies semantics. Evaluate on independently labeled recordings from different runs. First-person footage generally cannot establish the wearer's full-body running form.

## Combine observations with watch data

After verifying alignment, connect reviewed visual events to recorded workout measurements. Keep uncertainty explicit. A pace change beside stairs is an association; it does not prove fatigue. Compare the same section across repeated sessions while recording conditions and athlete intent.

## Optimization suggestions

A future agent could suggest testable adjustments for athlete or coach review: compare pacing choices on a repeated climb, reduce avoidable time spent searching equipment at a stop, or plan a more consistent aid-station routine. Each suggestion should cite observations, disclose missing context and propose how to evaluate the next run. Do not claim performance gains without a study or derive medical prescriptions from footage.

## Expansion sequence

1. Collect consented video and workout pairs and validate synchronization.
2. Add reviewed scene descriptions and retrieval over clips.
3. Evaluate repeated-route comparisons with independent labels.
4. Add coach-reviewed optimization experiments.
5. Consider native HealthKit/camera integrations and secure hosted processing after privacy and operational review.

## Beyond running

These are proposed applications of the evidence-review concept, not features of the current sports prototype.

### Rehabilitation review after a stroke or accident

The practical gap is home practice between appointments. A possible workflow would pair a recording of a therapist-prescribed walking or sit-to-stand task with suitable, validated wearable measurements. A fixed camera should show the whole movement; a runner's first-person camera is not a substitute for that view. With consent, a physiotherapist could revisit a pause, compare matched sessions, and discuss perceived fatigue with the patient. The intended outcome is a better-informed follow-up.

This extension requires clinical partners, task-specific measurement validation, secure access and retention, and prospective evaluation. A clinician would decide how to interpret the evidence and whether to reassess the task. The prototype does not diagnose stroke effects, evaluate medical safety, prescribe exercise or automatically change treatment. Consumer-watch heart rate, SpO₂ or temperature should not be treated as validated clinical measurements by default.

[WHO's rehabilitation overview](https://www.who.int/news-room/fact-sheets/detail/rehabilitation) describes person-centered rehabilitation after illness and injury, including support in home settings. It supports the general setting, not the effectiveness of RaceTime Replay.

### Workplace training and field inspections

An instructor could revisit a difficult task step with a learner; a field team could locate a relevant moment in an inspection recording. Each use case needs its own observation labels, data schema, permissions and evaluation. Collect wearable measurements only when they answer a specific, agreed question. Avoid treating physiological readings as an employee performance score.
