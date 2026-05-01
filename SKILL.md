---
name: opc-team-init
description: Initialize or refresh an OPC agent team for Hermes or OpenClaw. Use when the user wants coordinator/researcher/writer/builder long-running agents, user-defined peer agents such as growth-agent or secretary, shared Wiki memory, Discord channel-based proposal intake, and Subagent delegation/reporting rules that conserve main-agent context.
license: MIT
metadata:
  version: 0.2.1
---

# OPC Team Init

## Overview

Use this skill to bootstrap or refresh an OPC Agent Team for Hermes or OpenClaw:

- Four long-running agents: `coordinator`, `researcher`, `writer`, `builder`.
- Optional user-defined peer agents, generated from the user's needs.
- One user-selected shared vault with Wiki memory exposed as `WIKI_PATH`.
- Optional GStack and GBrain dependency detection with role-based skill distribution.
- Coordinator-owned Discord `#agent-proposals` intake.
- A Subagent delegation/reporting contract so temporary agents report back to exactly one owning agent instead of bloating context.

## Quick Start

When this skill is invoked, first ask where the shared vault should live, then ask whether the user wants to add custom peer agents. If yes, collect a short description for each custom agent and generate a spec using `references/custom-profiles.md`.

Run the initializer script from this skill. The default location can be overridden if the skill is installed somewhere else:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py"
```

Default shared vault path is `~/Documents/vault`. To make the user choose a shared vault interactively:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --select-vault
```

For a non-interactive vault choice:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --vault-path "$HOME/Documents/vault"
```

For OpenClaw, generate a non-invasive package under `~/.openclaw/opc-team`:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --target openclaw
```

With OpenClaw Discord channel routing, include the guild/server ID so the generated config patch can populate `channels.discord.guilds`:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --target openclaw \
  --discord-guild-id 345678901234567890 \
  --discord-channel-id 123456789012345678
```

Dependency checks default to prompt-only. The initializer never installs GStack or GBrain automatically:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --dependency-mode prompt
```

With real Discord values:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

With built-in example custom agents:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

With an LLM-generated custom agent spec:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --custom-profile-spec /path/to/custom-profiles.json
```

Only pass `--discord-bot-token` if the user explicitly provides the token in this turn. Do not invent, search for, or expose tokens.

## Workflow

1. Choose target: default to `--target hermes`; use `--target openclaw` when the user asks for OpenClaw.
2. Default the shared vault to `~/Documents/vault`. If the user wants a different place, read `references/shared-vault.md`, then use `--select-vault` for an interactive terminal choice, `--vault-path` for a chosen vault root, or `--wiki-path` only when the user wants an exact absolute Wiki directory.
3. Read `references/dependencies.md` and `references/skill-distribution.md` before changing dependency or role-skill behavior.
4. Run the script with defaults unless the user gives a different home path, vault path, Wiki path, dependency root, or Discord IDs.
5. Ask whether to add custom peer agents. If yes, read `references/custom-profiles.md`, generate JSON spec(s), and pass them with `--custom-profile-spec` or `--custom-profile-json`.
6. For Hermes, refresh role files, memory rules, config, `.env`, `skills.external_dirs`, and role-specific `skills.disabled` without deleting sessions or credentials.
7. For OpenClaw, read `references/openclaw.md`; generate an OpenClaw-compatible package under `~/.openclaw/opc-team` without mutating `.openclaw/openclaw.json`.
8. If Discord credentials are incomplete, leave safe placeholders and do not start the gateway.
9. If the user provides real Discord values and asks to start Hermes gateway, run with `--start-gateway`.
10. By default, the Hermes target seeds missing profile `auth.json` from the default Hermes home so OAuth-backed models work across Profiles. Use `--no-copy-auth` only when the user wants each Profile authenticated separately.
11. Verify Hermes with:

```bash
hermes profile list
coordinator gateway status
```

Use `--run-chat-checks` only when the user wants a live Hermes model check; it spends model calls. Verify OpenClaw by inspecting `~/.openclaw/opc-team/manifest.json`, `agents.json`, `openclaw.config.patch.json5`, and `OPENCLAW_IMPORT.md`.

## Custom Profile Model

Custom Agents are peer agents, not children of the four core agents. In Hermes they are real Profiles. In OpenClaw they are generated as peer agent specs in the package. They serve specialized user needs and are registered into coordinator's routing table.

- Do not require `parent_profile`.
- Let the LLM generate the custom agent from the user's description.
- A custom agent may spawn temporary Subagents, but those Subagents report only to that custom agent.
- Discord defaults to one bot token owned by coordinator; custom agents are associated with distinct Discord channels through coordinator channel prompts.

Read `references/custom-profiles.md` before creating or changing custom agent specs.

## Dependency Model

GStack and GBrain are external MIT dependencies. Do not vendor or copy either project into this skill. The initializer detects them and distributes their skills by role.

- GStack missing: print the target-specific setup command, `./setup --host hermes` for Hermes and `./setup --host openclaw` for OpenClaw.
- GBrain missing: print the agent install guide at `https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md`.
- Hermes: GStack skills are expected under `~/.hermes/skills/gstack*`; GBrain skills are added through `skills.external_dirs`.
- OpenClaw: GStack skills are expected under `~/.openclaw/skills/gstack` or `~/gstack/openclaw/skills`; GBrain can be loaded from `~/gbrain/openclaw.plugin.json` plus `~/gbrain/skills`.
- OpenClaw: dependency state, real OpenClaw skill IDs, per-agent directories, workspaces, `bindings`, `skills.load.extraDirs`, and `channels.discord` are written into the generated package and config patch.

Read `references/dependencies.md` and `references/skill-distribution.md` before changing this behavior.

## Subagent Model

All core and custom agents may spawn temporary Subagents when work is independent, context-heavy, or parallelizable. In Hermes this uses delegation toolsets; in OpenClaw this is a prompt/reporting contract. Subagents must return a compact report to exactly one owning agent.

Read `references/subagent-reporting.md` before changing the delegation prompt, report format, or routing policy.

## Safety Rules

- Never write secrets into `SOUL.md`, `MEMORY.md`, Wiki files, or `config.yaml`.
- Keep Discord bot token only in the coordinator `.env`.
- Keep project state in the shared Wiki, not in role memory.
- Do not delete existing Profiles, sessions, memories, or skills during refresh.
- Do not connect researcher/writer/builder to Discord unless the user explicitly asks for separate bots and channel policy.
- Do not mutate OpenClaw's live `openclaw.json` from this skill; generate the package and let the user/OpenClaw import path consume it.
