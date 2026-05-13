# Clean-Room Process

1. Observe game behavior through the emulator boundary.
2. Store raw evidence only in `evidence/private/`.
3. Convert observations into redacted metadata and abstract mechanics without exposing frame or crop paths.
4. Generate original asset recipes with explicit anti-similarity rules and human review requirements.
5. Implement the React Native prototype from mechanics and recipes, not from copyrighted assets.
6. Validate behavior with timing, state, event, and scoring tolerances instead of any pixel-perfect comparison.
