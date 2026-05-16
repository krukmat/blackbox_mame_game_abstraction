# Prompt 10 - Boot Calibration Spike

```text
Create a technical spike for boot calibration. Do not fully implement unless the required signals are already available.

Goal:

Reduce fragile hand-authored frame timings in plans such as boot-only or gameplay startup plans.

Deliverable:

Create a markdown design note:

- docs/boot_calibration_spike.md

Content:

1. Current timing problem.
2. Existing files involved in boot/start timing.
3. What private evidence can be used internally.
4. What public metadata can be emitted safely.
5. Candidate strategies:
   - fixed delay baseline;
   - visual diff stabilization;
   - credit/start prompt detection;
   - controllability probe;
   - hybrid manual-confirmation approach.
6. Recommended first implementation.
7. Risks and false positives.
8. Acceptance criteria.

Constraints:

- Do not move screenshots/video/audio to public specs.
- Do not implement fragile heuristics without tests.
- Do not change existing plans yet.

After writing the spike, summarize the recommended MVP for `blackbox calibrate-boot`.
```
