# Legal Guardrails

- Do not extract, export, recolor, transform, or reuse copyrighted sprites.
- Do not commit ROMs, screenshots, videos, audio captures, emulator save states, or raw frame captures.
- Keep all private evidence local under `evidence/private/`.
- Do not expose frame paths, crop paths, or raw image references in public specs.
- Asset generation must consume abstract recipes only, never original sprite crops or derived images.
- React Native outputs must be independently themed and use newly created assets.
- Public outputs reject blocked capture/media extensions such as `.png`, `.jpg`, `.mp4`, `.avi`, `.zip`, `.state`, and `.sav`.
- Generated asset recipes must include prohibited similarity rules and `human_review_required: true`.
