RaceTime Replay helps runners revisit the moments behind their workout numbers. Upload a first-person recording and workout data, then scrub through a shared timeline of video, heart rate, personal training zones, pace, cadence, elevation, running power and optional sensor readings.

### The problem
A watch can show where pace changed. A camera can show what was visible. The two records usually live apart, leaving an athlete to search footage and compare timestamps manually. A stop, a turn, missing GPS, and a camera pause can produce very different stories. RaceTime Replay brings the evidence together before drawing conclusions.

### Who it helps
The first audience is trail runners and endurance athletes reviewing their own sessions. Coaches can use shared, consented recordings to discuss specific moments with an athlete. Crew members can review event clips. Researchers and AI builders can study how a system behaves when multiple sources disagree.

### Why someone would care
Clicking a suspicious interval is more useful than scrubbing an entire recording. Linking a statement to an actual clip makes it easier to check. Showing missing data and conflicting sources helps prevent confident explanations based on an incomplete record. These are intended benefits; time savings and coaching outcomes have not yet been measured in a user study.

### Why now
GoPro and Insta360 action cameras, iPhones, and camera-equipped Meta glasses make first-person recording accessible in several familiar forms. Garmin, COROS, Suunto, Apple Watch and other sports watches can record workout measurements during the same activity. Compatible external sensors can contribute explicitly sourced core-temperature readings; SpO₂ is optional and may be intermittent. This creates an opportunity to reuse recordings for reflection as well as memories. Recording duration, battery, field of view, stabilization and export support differ across devices. RaceTime accepts exported video files; it does not claim a direct integration with every device or continuous recording support.

### A personal starting point
Siva Babu brings together an interest in running and an engineering focus on observability. The project applies that habit of investigating signals to a run: collect observations, align them, inspect disagreements, and explain what the evidence supports. The published benchmark uses generated fixtures; it does not represent personal workout results.

### What the first version does
The working prototype aligns a video with workout samples, measures visual motion with OpenCV, highlights sustained heart-rate zone changes, compares readings and retains diagnostic quality checks, and lets a person review the supporting clip. A bounded agent retrieves relevant records and explains the measured events with references. The result separates measured observations, a possible interpretation and a proposed experiment, such as comparing steadier effort on a similar segment. This is a hypothesis to review, not a proven performance gain. Review notes and source files stay on the app host; optional cloud features have explicit data boundaries.

### Where this can grow
A future vision model could summarize visible trail surfaces, turns, queues and other events. A later system could combine verified scene observations with watch measurements, comparable past sessions, conditions and athlete goals to propose experiments or optimization suggestions. For example, it might help an athlete compare pacing on the same climb or review time spent at an aid station. These suggestions would need uncertainty estimates, repeat-run evaluation and athlete or coach review. The current release does not infer fatigue, diagnose injury, prescribe training, or claim to recognize terrain automatically.

### Optional AI infrastructure
Nebius Token Factory can provide the language model that writes a draft from selected evidence. The Python app supports provider selection and keeps measured observations visible. A future vision-capable deployment could label reviewed frames before a separate model combines those labels with watch measurements. The current Nebius adapter sends text only and needs a local API key and current model ID.

See [performance review](PERFORMANCE_REVIEW.md) for the supported metrics, sensor boundaries and how to evaluate proposed improvements.
