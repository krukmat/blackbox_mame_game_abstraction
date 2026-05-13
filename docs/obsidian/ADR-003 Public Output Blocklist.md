# ADR-003 — Public Output Extension and Directory Blocklist

tags: #adr #guardrails

Status: **Accepted** | Date: 2026-05-13

> See the full ADR at `docs/adr/ADR-003-public-output-blocklist.md`

## Summary

Three complementary blocklists prevent copyrighted content from leaking into public tracked outputs.

| Check | What it blocks |
|-------|----------------|
| Extension blocklist | Writing `.png`, `.avi`, `.sav`, `.rom`, etc. to tracked paths |
| Directory blocklist | Writing any file into directories named `frames/`, `video/`, `crops/`, etc. |
| Path marker scan | Embedding `evidence/private/`, `/frames/`, `/crops/` as string values in public metadata |

All three are needed because they catch different attack surfaces.

## The Static Set Problem

The extension blocklist is static. New evidence types (e.g., `.webp`) require manual additions to `BLOCKED_PUBLIC_SUFFIXES` in `guardrails.py`.

## Related

- [[Guardrails]]
- [[Private vs Public Boundary]]
- [[ADR-001 Clean-Room Layered Architecture]]
- [[ADR-002 Private URI Scheme]]
