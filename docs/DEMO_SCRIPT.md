# Five minute demonstration

1. Explain the problem: a camera records context and a watch records measurements, but reviewing the same moment in both takes manual work. The first audience is a runner reviewing their own session.
2. Open the app. State clearly that this is a generated 90-second test fixture, not a real race. Show the two input types and the synchronization offset.
3. Click the stop at about 20 seconds. The player, chart and route position share the video clock. Inspect the candidate and record a human review.
4. Click the disagreement at 45 seconds. The camera moves while the synthetic watch says zero speed. Explain why the agent should not assert a single cause. Show the missing-speed interval.
5. Ask where the stops occurred. Open the evidence workflow to show routing, retrieval, references and local node timings. Ask an instruction-override question and show the refusal.
6. Open Build and evaluation. Explain the speed-only baseline versus fused evidence, the synthetic-data limitation, the LoRA result and why it was not promoted. Explain the LangSmith quota blocker rather than presenting a false trace link.
7. Close with the future: reviewed visual scene summaries, repeated-route comparisons and athlete/coach-reviewed optimization experiments. Those are extensions, not features claimed in this release.
