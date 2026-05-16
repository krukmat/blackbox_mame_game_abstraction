# Prompt 06 - Add Portable Environment Config and Doctor Command

```text
Improve bootstrap portability without changing the core mapping architecture.

Scope:

The repo currently has scripts with local-machine assumptions. Add a portable configuration mechanism and a doctor/preflight command.

Tasks:

1. Add examples:

- .env.example
- blackbox.local.example.yaml

2. Refactor scripts that hardcode local paths, especially:

- scripts/launch_manual_capture.sh
- scripts/launch_manual_capture_autoboot.sh
- scripts/extract_frames.sh

3. Support environment variables for:

- MAME binary path;
- ROM path;
- ffmpeg path;
- output directory;
- source profile / driver where appropriate.

4. Add or extend a command:

```bash
blackbox doctor
```

or, if the repo already has equivalent preflight CLI conventions, follow that convention.

Doctor command should check:

- MAME binary exists and is executable;
- ffmpeg exists if frame extraction is requested;
- configured ROM path exists locally;
- public output paths do not point inside private evidence unless explicitly intended;
- no local absolute paths are written to public metadata.

Constraints:

- Do not commit user-specific paths.
- Do not move ROMs or private evidence.
- Do not include ROM names/content in public generated files beyond existing source profile abstractions.
- Existing tests must pass.

Add tests for config loading and path redaction if feasible.

After implementation, summarize how a new contributor should configure the repo locally.
```
