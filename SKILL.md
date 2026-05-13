---
name: opc-team-init
description: Initialize, refresh, or audit an OPC agent team for Hermes or OpenClaw. Use to handle requests like "set up agent team", "refresh my profiles", "build an OPC team", "install and configure OPC", "fix Discord gateway", "audit my Hermes setup", or similar. Covers Hermes profiles (default coordinator + researcher/writer/builder + custom peers like growth-agent or secretary), shared Wiki memory at WIKI_PATH, one-token Discord channel routing, gateway drift, and English / Simplified Chinese / Traditional Chinese profile content. English is the source of truth for all multilingual content.
license: MIT
metadata:
  version: 0.5.2
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
- A setup wrapper for install + configure flows. Codex skill installation has no reliable post-install hook, so setup is explicit through `scripts/opc_team_setup.py` or the fsSL-friendly `scripts/install_configure.sh`.
- Channel routing from a reusable team spec: the default/coordinator home channel is free-response; researcher, writer, builder, and custom Profile channels require mention and use auto-threading.
- A Subagent delegation/reporting contract so temporary agents report back to exactly one owning agent instead of bloating context.
- Three-language profile content: `--language en|zh-CN|zh-TW` (required for `--mode init`). English is the source of truth; the others are translations.
- Read-only audit (`--mode audit`) reports drift, missing profiles, residual multi-gateway LaunchAgents, and Discord channel profile/prompt coverage. Generated channel source-of-truth lives in `OPC_CHANNELS.json`.
- Specialist and custom Profile SOUL.md and MEMORY.md are written inside `<!-- BEGIN OPC MANAGED ... -->` ... `<!-- END OPC MANAGED ... -->` blocks; manual content outside the block is preserved across reruns. Pre-write snapshots land in `~/.hermes/.opc-backups/<timestamp>/` (last 10 retained).

## Quick Start

When this skill is invoked:

1. Prefer the setup wrapper when the user describes agent roles, channels, or shared vaults in natural language. Read `references/team-config.md`, convert the request into a JSON team spec, then run `scripts/opc_team_setup.py configure --team-spec <spec>`.
2. If the user asks for install + configure, run `scripts/opc_team_setup.py install-configure --team-spec <spec>`. Use the shell wrapper only for fsSL-style bootstrap.
3. For installs that already exist, keep the setup wrapper's audit-first behavior. It runs `--mode audit` before writes and refuses severe multi-gateway risk unless explicitly overridden.
4. For low-level direct refreshes, use `scripts/init_opc_team.py` as the source-of-truth engine.

There is no reliable Codex post-install lifecycle hook. Do not promise automatic configuration immediately after skill installation; provide an explicit setup command instead.

Setup from an installed skill:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/opc_team_setup.py" configure \
  --team-spec /path/to/opc-team.json
```

Install or reuse the skill, then configure:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/opc_team_setup.py" install-configure \
  --team-spec /path/to/opc-team.json
```

fsSL-style bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/Ancienttwo/opc-team-init/main/scripts/install_configure.sh \
  | OPC_TEAM_INIT_REPO_URL=https://github.com/Ancienttwo/opc-team-init.git \
    bash -s -- --team-spec /path/to/opc-team.json
```

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

With one-bot multi-channel routing, only `--discord-channel-id` is free-response. Other `--agent-channel` routes require mention and auto-thread:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language zh-CN \
  --discord-channel-id 100000000000000001 \
  --agent-channel researcher=100000000000000002 \
  --agent-channel writer=100000000000000003 \
  --agent-channel builder=100000000000000004 \
  --agent-channel secretary=100000000000000005 \
  --custom-profile-preset secretary
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
- Discord `channel_profiles` and `channel_prompts` coverage: which custom-profile channel IDs are wired into default config and which are missing or extra.
- Custom registry vs profile directory consistency.
- Wiki path validity (existence and presence of SCHEMA.md).
- Multi-gateway LaunchAgents in `~/Library/LaunchAgents/com.hermes.gateway*.plist`. More than one means a Discord bot-token conflict is likely.

## Workflow

1. Confirm `--language` (`en` / `zh-CN` / `zh-TW`). The script refuses `--mode init` without it. English is the source of truth; the others are translations.
2. If `~/.hermes/profiles/` already exists, run `--mode audit` first and show the user any `drift`, `legacy`, or LaunchAgent warnings before any write. `legacy` files will get a managed block appended on the next write; manual content outside the block is preserved.
3. Choose target: default to `--target hermes`; use `--target openclaw` when the user asks for OpenClaw.
4. Default the shared vault to `~/Documents/vault`. If the user wants a different place, read `references/shared-vault.md`, then use `--select-vault` for an interactive terminal choice, `--vault-path` for a chosen vault root, or `--wiki-path` only when the user wants an exact absolute Wiki directory.
5. For natural-language team setup, read `references/team-config.md` and generate one JSON team spec rather than manually composing many CLI flags.
6. Read `references/dependencies.md` and `references/skill-distribution.md` before changing dependency or role-skill behavior.
7. Run the script with defaults unless the user gives a different home path, vault path, Wiki path, dependency root, or Discord IDs.
8. Ask whether to add custom peer agents. If yes, read `references/custom-profiles.md`, generate JSON spec(s), and pass them with `--custom-profile-spec` or `--custom-profile-json`.
9. For Hermes, only the coordinator role rewrites/augments the user's default root `SOUL.md` and memory through a managed block. `researcher`/`writer`/`builder` and custom peer agents are refreshed in place inside their own per-profile managed blocks; `profiles/coordinator` is left as a legacy backup/template if it exists.
10. For OpenClaw, read `references/openclaw.md`; generate an OpenClaw-compatible package under `~/.openclaw/opc-team` without mutating `.openclaw/openclaw.json`.
11. If Discord credentials are incomplete, leave safe placeholders and do not start the gateway.
12. **Default to single-gateway mode.** Hermes does not allow two gateways to share a Discord bot token. The default coordinator gateway receives `discord.channel_profiles` for runtime routing and `discord.channel_prompts` for prompt/context injection for every specialist + custom Profile; researcher/writer/builder gateways are not started. Only pass `--multi-gateway` when each profile already has its own `DISCORD_BOT_TOKEN` in `profiles/<name>/.env`; the script will refuse otherwise.
13. If the user provides real Discord values and asks to start Hermes gateway, run with `--start-gateway`.
14. By default, the Hermes target seeds missing profile `auth.json` from the default Hermes home so OAuth-backed models work across Profiles. Use `--no-copy-auth` only when the user wants each Profile authenticated separately.
15. Before relying on OpenAI Codex GPT-5.x role/model routing, verify `hermes auth list` or `hermes status` shows `openai-codex` OAuth logged in. If missing, do not configure or refresh profiles that use `provider: openai-codex`; have the user authenticate or choose another provider first.
16. Verify Hermes with:

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
- Hermes Discord defaults to one bot token owned by default/coordinator-primary; custom agents are associated with distinct Discord channels through default `channel_profiles` runtime routes and compatible channel prompts.
- Custom Profile language follows the global `--language`; do not put a `language` field inside individual specs.
- OpenClaw Discord defaults to one bot token owned by the generated coordinator agent.

Read `references/custom-profiles.md` before creating or changing custom agent specs.

## Managed Blocks and Backups

`refresh_default_coordinator` and `refresh_profiles` write into specific marker pairs and never touch content outside them. Specialist + custom profile files use `<!-- BEGIN OPC MANAGED: <profile> SOUL -->` and the matching `END` marker; the default coordinator's SOUL/MEMORY use the legacy `OPC_TEAM_DEFAULT_COORDINATOR_*` markers.

YAML config writes are scoped to a fixed allowlist of keys (`skills.disabled`, `skills.external_dirs`, `delegation`, `platform_toolsets.cli`, `discord.require_mention`, `discord.auto_thread`, `discord.reactions`, `discord.free_response_channels`, `discord.channel_profiles`, `discord.channel_prompts`). Other keys in `config.yaml` are preserved. The default config's `discord.channel_profiles` and `discord.channel_prompts` are merged dict-wise, so manual entries the user added are kept.

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
- A single Hermes gateway holds the Discord bot token; starting a second gateway with the same token will fail. Default to single-gateway mode and use `discord.channel_profiles` for per-channel Profile runtime routing.
- Only the default/coordinator home channel should be listed in `discord.free_response_channels`. Specialist and custom channels should have `channel_profiles` plus `channel_prompts`, but stay mention-required so Hermes can auto-create threads.
- Keep project state in the shared Wiki, not in role memory.
- Do not delete existing Profiles, sessions, memories, or skills during refresh.
- Do not connect researcher/writer/builder to Discord unless the user explicitly asks for separate bots and channel policy.
- Do not mutate OpenClaw's live `openclaw.json` from this skill; generate the package and let the user/OpenClaw import path consume it.
