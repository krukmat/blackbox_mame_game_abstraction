# Prompt 11 - First PR Review Prompt

Use this after Codex/Claude Code has implemented Phase 1.

```text
Review the current branch as a senior maintainer.

Focus on whether the implementation respects the ADR:

- layered model: device_profile -> controller_profile -> game_action_profile -> compiled input plan;
- no rewrite of MAME execution path;
- clean-room safety;
- no absolute local paths in public files;
- sample profiles are minimal and understandable;
- generated input plan is compatible with existing input_planner.py;
- tests cover validation and compilation;
- CLI commands are consistent with existing style;
- documentation is concise and contributor-oriented.

Find issues in priority order:

1. correctness bugs;
2. clean-room or path-leak risks;
3. schema/model inconsistencies;
4. broken backward compatibility;
5. confusing contributor UX;
6. overengineering.

For each issue, provide:

- file/path;
- problem;
- why it matters;
- exact recommended change.

Do not propose unrelated rewrites.
```
