---
name: opc-team-init
description: Initialize, refresh, or audit an OPC agent team for Hermes or OpenClaw. Use this skill whenever the user wants to set up or rework Hermes profiles (default coordinator + researcher/writer/builder + custom peers like growth-agent or secretary), wire shared Wiki memory at WIKI_PATH, configure Discord channel routing through one bot token, debug why a Hermes gateway stopped working, diagnose drift in existing ~/.hermes profiles, or write profile content in English / Simplified Chinese / Traditional Chinese — even if they phrase it as "set up agent team", "refresh my profiles", "build an OPC team", "fix Discord gateway", "audit my Hermes setup", or similar. English is the source of truth for all multilingual content.
license: MIT
metadata:
  version: 0.4.0
---

# OPC Team Init

## Overview

Use this skill to bootstrap or refresh an OPC Agent Team for Hermes or OpenClaw:

- Hermes: the user's own default agent becomes `coordinator-primary`; long-running peer Profiles are `researcher`, `writer`, and `builder`.
- Only the coordinator role is implemented by rewriting/augmenting the user's default Hermes agent. `researcher`, `writer`, `builder`, and all custom agents are created and refreshed as real Hermes Profiles.
- OpenClaw: generate explicit `coordinator`, `researcher`, `writer`, and `builder` agents in the package.
- Optional user-defined peer agents, generated from the user's needs.
- One user-selected shared vault with Wiki memory exposed as `WIKI_PATH`.
- Optional GStack, GBrain, and Waza dependency detection with role-based skill distribution.
- Hermes default-owned Discord `#agent-proposals` intake.
- A Subagent delegation/reporting contract so temporary agents report back to exactly one owning agent instead of bloating context.
- Three-language profile content: `--language en|zh-CN|zh-TW` (required for `--mode init`). English is the source of truth; the others are translations.
- Read-only audit (`--mode audit`) reports drift, missing profiles, residual multi-gateway LaunchAgents, and Discord channel-prompt coverage.
- Specialist and custom Profile SOUL.md and MEMORY.md are written inside `<!-- BEGIN OPC MANAGED ... -->` ... `<!-- END OPC MANAGED ... -->` blocks; manual content outside the block is preserved across reruns. Pre-write snapshots land in `~/.hermes/.opc-backups/<timestamp>/` (last 10 retained).

## Quick Start

When this skill is invoked:

1. Confirm the **target language** for profile and Wiki content (`en` / `zh-CN` / `zh-TW`). Infer from the user's current message language as a hint, but always confirm. English is the source of truth.
2. Ask where the shared vault should live.
3. Ask whether the user wants to add custom peer agents. If yes, collect a short description for each and generate a spec using `references/custom-profiles.md`.
4. For installs that already exist, run `--mode audit` first (see Audit section) before any write.

Run the initializer script from this skill. The default location can be overridden if the skill is installed somewhere else:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en
```

The script refuses to run `--mode init` without `--language`. Use `zh-CN` for Simplified Chinese or `zh-TW` for Traditional Chinese.

Default shared vault path is `~/Documents/vault`. To make the user choose a shared vault interactively:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language zh-CN \
  --select-vault
```

For a non-interactive vault choice:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --vault-path "$HOME/Documents/vault"
```

For OpenClaw, generate a non-invasive package under `~/.openclaw/opc-team`:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language zh-TW \
  --target openclaw
```

With OpenClaw Discord channel routing, include the guild/server ID so the generated config patch can populate `channels.discord.guilds`:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --target openclaw \
  --discord-guild-id 345678901234567890 \
  --discord-channel-id 123456789012345678
```

Dependency checks default to prompt-only. The initializer never installs GStack, GBrain, or Waza automatically:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --dependency-mode prompt
```

To point at an explicit Waza bundle root or direct `skills/` directory:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --waza-root "$HOME/.claude/skills/waza"
```

With real Discord values:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

With built-in example custom agents:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language zh-CN \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

With an LLM-generated custom agent spec:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --custom-profile-spec /path/to/custom-profiles.json
```

Only pass `--discord-bot-token` if the user explicitly provides the token in this turn. Do not invent, search for, or expose tokens.

## Audit (read-only)

Use `--mode audit` to inspect an existing install without writing anything. `--language` is not required for audit; the script probes the existing default `SOUL.md` to guess which language is currently in use.

```bash
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --hermes-home "$HOME/.hermes" \
  --mode audit
```

Add `--audit-json` for machine-readable output. Exit codes: `0` = clean, `1` = drift or missing profiles, `2` = severe risk (multiple Hermes gateway LaunchAgents fighting for the same bot token).

The audit reports:

- Per-profile SOUL.md and MEMORY.md status: `clean` (matches template hash), `drift` (managed block exists but content was edited), `legacy` (no managed block — pre-v0.4 file or pure manual content), or `missing`.
- Lines of manual content sitting outside each managed block (preserved by init).
- Discord `channel_prompts` coverage: which custom-profile channel IDs are wired into default config and which are missing or extra.
- Custom registry vs profile directory consistency.
- Wiki path validity (existence and presence of SCHEMA.md).
- Multi-gateway LaunchAgents in `~/Library/LaunchAgents/com.hermes.gateway*.plist`. More than one means a Discord bot-token conflict is likely.

## Workflow

1. Confirm `--language` (`en` / `zh-CN` / `zh-TW`). The script refuses `--mode init` without it. English is the source of truth; the others are translations.
2. If `~/.hermes/profiles/` already exists, run `--mode audit` first and show the user any `drift`, `legacy`, or LaunchAgent warnings before any write. `legacy` files will get a managed block appended on the next write; manual content outside the block is preserved.
3. Choose target: default to `--target hermes`; use `--target openclaw` when the user asks for OpenClaw.
4. Default the shared vault to `~/Documents/vault`. If the user wants a different place, read `references/shared-vault.md`, then use `--select-vault` for an interactive terminal choice, `--vault-path` for a chosen vault root, or `--wiki-path` only when the user wants an exact absolute Wiki directory.
5. Read `references/dependencies.md` and `references/skill-distribution.md` before changing dependency or role-skill behavior.
6. Run the script with defaults unless the user gives a different home path, vault path, Wiki path, dependency root, or Discord IDs.
7. Ask whether to add custom peer agents. If yes, read `references/custom-profiles.md`, generate JSON spec(s), and pass them with `--custom-profile-spec` or `--custom-profile-json`.
8. For Hermes, only the coordinator role rewrites/augments the user's default root `SOUL.md` and memory through a managed block. `researcher`/`writer`/`builder` and custom peer agents are refreshed in place inside their own per-profile managed blocks; `profiles/coordinator` is left as a legacy backup/template if it exists.
9. For OpenClaw, read `references/openclaw.md`; generate an OpenClaw-compatible package under `~/.openclaw/opc-team` without mutating `.openclaw/openclaw.json`.
10. If Discord credentials are incomplete, leave safe placeholders and do not start the gateway.
11. **Default to single-gateway mode.** Hermes does not allow two gateways to share a Discord bot token. The default coordinator gateway also receives `discord.channel_prompts` for every specialist + custom Profile; researcher/writer/builder gateways are not started. Only pass `--multi-gateway` when each profile already has its own `DISCORD_BOT_TOKEN` in `profiles/<name>/.env`; the script will refuse otherwise.
12. If the user provides real Discord values and asks to start Hermes gateway, run with `--start-gateway`.
13. By default, the Hermes target seeds missing profile `auth.json` from the default Hermes home so OAuth-backed models work across Profiles. Use `--no-copy-auth` only when the user wants each Profile authenticated separately.
14. Before relying on OpenAI Codex GPT-5.x role/model routing, verify `hermes auth list` or `hermes status` shows `openai-codex` OAuth logged in. If missing, do not configure or refresh profiles that use `provider: openai-codex`; have the user authenticate or choose another provider first.
15. Verify Hermes with:

```bash
hermes profile list
hermes gateway status
```

Use `--run-chat-checks` only when the user wants a live Hermes model check; it spends model calls. Verify OpenClaw by inspecting `~/.openclaw/opc-team/manifest.json`, `agents.json`, `openclaw.config.patch.json5`, and `OPENCLAW_IMPORT.md`.

## Custom Profile Model

Custom Agents are peer agents, not children of the core agents. In Hermes they are real Profiles routed by default/coordinator-primary. In OpenClaw they are generated as peer agent specs in the package. They serve specialized user needs and are registered into the routing table.

- Do not require `parent_profile`.
- Do not allow a custom Profile named `default`, `coordinator`, `researcher`, `writer`, or `builder`.
- Let the LLM generate the custom agent from the user's description.
- A custom agent may spawn temporary Subagents, but those Subagents report only to that custom agent.
- Hermes Discord defaults to one bot token owned by default/coordinator-primary; custom agents are associated with distinct Discord channels through default channel prompts.
- Custom Profile language follows the global `--language`; do not put a `language` field inside individual specs.
- OpenClaw Discord defaults to one bot token owned by the generated coordinator agent.

Read `references/custom-profiles.md` before creating or changing custom agent specs.

## Managed Blocks and Backups

`refresh_default_coordinator` and `refresh_profiles` write into specific marker pairs and never touch content outside them. Specialist + custom profile files use `<!-- BEGIN OPC MANAGED: <profile> SOUL -->` and the matching `END` marker; the default coordinator's SOUL/MEMORY use the legacy `OPC_TEAM_DEFAULT_COORDINATOR_*` markers.

YAML config writes are scoped to a fixed allowlist of keys (`skills.disabled`, `skills.external_dirs`, `delegation`, `platform_toolsets.cli`, `discord.require_mention`, `discord.auto_thread`, `discord.reactions`, `discord.free_response_channels`, `discord.channel_prompts`). Other keys in `config.yaml` are preserved. The default config's `discord.channel_prompts` is merged dict-wise, so manual entries the user added are kept.

Before any write, the script snapshots SOUL/MEMORY/config and the routing table to `~/.hermes/.opc-backups/<timestamp>/`. The newest 10 snapshots are kept; older ones are pruned automatically.

## Dependency Model

GStack, GBrain, and Waza are external dependencies. Do not vendor or copy any of them into this skill. The initializer detects them and distributes their skills by role.

- GStack missing: print the target-specific setup command, `./setup --host hermes` for Hermes and `./setup --host openclaw` for OpenClaw.
- GBrain missing: print the agent install guide at `https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md`.
- Waza missing: print `npx skills add tw93/Waza -a codex -g -y`.
- Waza source-of-truth: only an explicit Waza bundle counts as the dependency. Same-name legacy skills are left in place, warned about, and never overwritten automatically.
- Hermes: GStack skills are expected under `~/.hermes/skills/gstack*`; GBrain skills are added through `skills.external_dirs`; Waza is added through `skills.external_dirs` only when the bundle is present and no same-name runtime collisions exist.
- Hermes: Waza passive skill exposure is limited to the core four roles. Custom peer agents do not inherit Waza automatically in this version.
- OpenClaw: GStack skills are expected under `~/.openclaw/skills/gstack` or `~/gstack/openclaw/skills`; GBrain can be loaded from `~/gbrain/openclaw.plugin.json` plus `~/gbrain/skills`; Waza can be loaded from a detected external `skills/` directory.
- OpenClaw: dependency state, real OpenClaw skill IDs, Waza skill names, per-agent directories, workspaces, `bindings`, `skills.load.extraDirs`, and `channels.discord` are written into the generated package and config patch.

Read `references/dependencies.md` and `references/skill-distribution.md` before changing this behavior.

## Subagent Model

All core and custom agents may spawn temporary Subagents when work is independent, context-heavy, or parallelizable. In Hermes this uses delegation toolsets; in OpenClaw this is a prompt/reporting contract. Subagents must return a compact report to exactly one owning agent.

Read `references/subagent-reporting.md` before changing the delegation prompt, report format, or routing policy.

## Safety Rules

- Never write secrets into `SOUL.md`, `MEMORY.md`, Wiki files, or `config.yaml`.
- Keep Hermes Discord bot token only in the default `.env`; do not copy it into researcher/writer/builder/custom Profile `.env` files. The exception is `--multi-gateway` mode, which requires a unique token per profile in each `profiles/<name>/.env`.
- A single Hermes gateway holds the Discord bot token; starting a second gateway with the same token will fail. Default to single-gateway mode and use `discord.channel_prompts` to route per-channel role behavior.
- Keep project state in the shared Wiki, not in role memory.
- Do not delete existing Profiles, sessions, memories, or skills during refresh.
- Do not connect researcher/writer/builder to Discord unless the user explicitly asks for separate bots and channel policy.
- Do not mutate OpenClaw's live `openclaw.json` from this skill; generate the package and let the user/OpenClaw import path consume it.
