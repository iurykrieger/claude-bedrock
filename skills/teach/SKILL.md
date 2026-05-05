---
name: teach
description: >
  [DEPRECATED] Backward-compatibility alias for /bedrock:learn.
  Use /bedrock:learn to ingest external sources into the vault.
  Triggers: "bedrock teach", "bedrock-teach", "/bedrock:teach"
user_invocable: true
allowed-tools: Skill
---

# /bedrock:teach — Backward-Compatibility Alias

> [!warning] Deprecated
> `/bedrock:teach` has been renamed to `/bedrock:learn`.
> This alias keeps working, but use `/bedrock:learn` in new workflows.

Delegating to `/bedrock:learn` with all arguments received...

Use the Skill tool to invoke `bedrock:learn`, passing all arguments received by this skill unchanged.
