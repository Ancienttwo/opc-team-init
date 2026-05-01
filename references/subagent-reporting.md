# Subagent Reporting Contract

Use this reference when initializing or revising OPC Agent Team delegation rules for Hermes or OpenClaw.

## When To Spawn

Spawn a temporary Subagent when a task is:

- Independent from the main Profile's immediate next step.
- Context-heavy enough that loading raw files/sources into the main thread would be wasteful.
- Naturally parallel, such as checking multiple sources, auditing separate modules, or producing a bounded implementation slice.
- Disposable: the Subagent should not need long-term identity or memory after reporting.

Do not spawn a Subagent when the next main-agent action depends on the answer immediately, when the task needs sensitive credentials, or when one clear local edit is faster than coordination overhead.

## Report Target

Every Subagent must report to exactly one owning agent:

- `coordinator`: plans, routing, status, decisions, integration summaries.
- `researcher`: evidence, source notes, contradictions, uncertainty.
- `writer`: outlines, drafts, editorial variants, audience adaptation.
- `builder`: patches, test results, implementation risks, code review findings.
- `<custom-profile-name>`: the specialized owner that spawned the Subagent.

## Required Report Shape

Subagent reports should be compact and copyable:

```markdown
## Subagent Report

Target: coordinator | researcher | writer | builder | <custom-profile-name>
Task:
Result:
Evidence / Files:
Open Questions:
Recommended Next Action:
Wiki Update Needed: yes | no
```

## Memory Boundary

Temporary Subagents do not write long-term role memory. The receiving owning agent decides whether durable information belongs in the shared Wiki.

## Delegation Prompt Pattern

Use a bounded prompt:

```text
You are a temporary Subagent for the OPC Agent Team.
Owning agent target: <coordinator|researcher|writer|builder|custom-profile-name>.
Task: <bounded task>.
Constraints: do not modify unrelated files; do not write long-term role memory; report only the result.
Return the Subagent Report shape exactly.
```

For OpenClaw, use the same report shape as a prompt-level contract. The OpenClaw package records each owning agent in `agents.json` so temporary work can be summarized back to the correct core or custom agent.
