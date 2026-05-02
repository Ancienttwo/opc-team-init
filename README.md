# OPC Team Init

Initialize or refresh an OPC-style multi-agent team for Hermes or OpenClaw.

The default team is:

- default Hermes agent as `coordinator-primary`: goals, routing, synthesis, archive
- `researcher`: evidence, verification, uncertainty
- `writer`: structure, reader-facing content
- `builder`: implementation, debugging, tests

Only the coordinator role is implemented by rewriting/augmenting the user's default Hermes agent. All other Hermes roles, including custom agents, are created as real Profiles.

It also supports user-defined peer agents such as `growth-agent` and `secretary`, shared Wiki memory, Discord proposal intake, and temporary Subagent reporting rules.

Profile content can be written in English, Simplified Chinese, or Traditional Chinese. English is the source of truth.

## Install

Install this folder as a Codex skill under:

```bash
$HOME/.codex/skills/opc-team-init
```

The skill is MIT licensed. See [LICENSE](LICENSE).

## Quick Start

Hermes target:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en
```

`--language` is **required** for `--mode init` (the default mode). Choose `en`, `zh-CN`, or `zh-TW`. The `--mode audit` subcommand does not need it.

OpenClaw target:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language zh-TW \
  --target openclaw
```

The default shared Wiki path is:

```text
$HOME/Documents/vault
```

Choose a vault interactively:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language zh-CN \
  --select-vault
```

Use an exact Wiki directory:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en \
  --wiki-path "/absolute/path/to/vault"
```

## Languages

`--language en|zh-CN|zh-TW` controls which copy is written into:

- `~/.hermes/SOUL.md` and `~/.hermes/memories/MEMORY.md` (default coordinator)
- `~/.hermes/profiles/{researcher,writer,builder}/SOUL.md` and `memories/MEMORY.md`
- `~/.hermes/profiles/<custom>/SOUL.md` and `memories/MEMORY.md`
- `~/.hermes/OPC_ROUTING_TABLE.md`
- `~/.hermes/DISCORD_AGENT_PROPOSALS_SETUP.md`
- Default `discord.channel_prompts` strings injected into `~/.hermes/config.yaml`
- Wiki seed pages: `SCHEMA.md`, `index.md`, `log.md`, `concepts/*.md`, `entities/custom-profiles.md`, `projects/opc-agent-team-operating-model.md`
- OpenClaw package `agents/*.md`, `agent-dirs/*/SOUL.md|MEMORY.md`, `routing-table.md`, `subagent-reporting.md`, `discord-channel-routing.json`

English is the source of truth; `zh-CN` and `zh-TW` are translations. Custom-profile language follows the global flag — do not put a `language` field inside individual specs.

## Audit (read-only)

To inspect an existing install without writing anything:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --hermes-home "$HOME/.hermes" \
  --mode audit
```

Add `--audit-json` for machine-readable output. Exit codes: `0` clean, `1` drift or missing, `2` severe (multiple Hermes gateway LaunchAgents fighting over a shared bot token).

The audit reports:

- Per-profile SOUL/MEMORY status: `clean`, `drift` (managed block edited), `legacy` (no managed block — pre-v0.4 file or pure manual content), or `missing`.
- Lines of manual content sitting outside each managed block (preserved across reruns).
- Discord `channel_prompts` coverage vs the registered custom profiles.
- Custom registry vs profile directory consistency.
- Wiki path validity.
- Multi-gateway LaunchAgents in `~/Library/LaunchAgents/com.hermes.gateway*.plist`.

## Custom Agents

Add built-in custom peer agents:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language zh-CN \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

Add your own custom agent from JSON:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en \
  --custom-profile-spec /path/to/custom-profiles.json
```

Custom agents are peers, not children of the core agents. They are created as Hermes Profiles and may not use reserved names such as `default`, `coordinator`, `researcher`, `writer`, or `builder`. Temporary Subagents only report to their immediate owning agent.

## Dependencies

GStack and GBrain are detected, not installed automatically.

Hermes GStack setup:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host hermes
```

OpenClaw GStack setup:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host openclaw
```

GBrain agent install guide:

```text
https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md
```

Dependency mode:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en \
  --dependency-mode prompt
```

Use `--dependency-mode strict` in CI-style checks.

## Discord

Hermes does not allow two gateways to share a Discord bot token; a second `hermes gateway start` with the same token will fail. The default mode is therefore **single-gateway**: only the default coordinator gateway connects to Discord, and per-channel role behavior is driven by `discord.channel_prompts` in `~/.hermes/config.yaml`. Specialist and custom Profiles never start their own gateway by default.

Hermes proposal channel:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

OpenClaw channel routing:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --language en \
  --target openclaw \
  --discord-guild-id 345678901234567890 \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

`--multi-gateway` is an advanced opt-in. It requires each profile to already have its own `DISCORD_BOT_TOKEN` line in `~/.hermes/profiles/<name>/.env`; the script refuses to start per-profile gateways otherwise.

Do not commit real bot tokens.

## Managed Blocks and Backups

Specialist and custom profile `SOUL.md` and `memories/MEMORY.md` are written inside `<!-- BEGIN OPC MANAGED: <profile> SOUL -->` ... `<!-- END OPC MANAGED: <profile> SOUL -->` blocks. Manual content outside those blocks is preserved across reruns; rerunning the script replaces the block in place. The default coordinator's SOUL/MEMORY use the legacy `OPC_TEAM_DEFAULT_COORDINATOR_*` markers.

`config.yaml` writes are scoped to a fixed allowlist (`skills.disabled`, `skills.external_dirs`, `delegation`, `platform_toolsets.cli`, plus `discord.require_mention/auto_thread/reactions/free_response_channels/channel_prompts`). Other keys are not touched. The default `discord.channel_prompts` map is merged dict-wise so manual entries the user added are kept.

Before each refresh, the script snapshots SOUL/MEMORY/config/routing-table to `~/.hermes/.opc-backups/<timestamp>/` and prunes older snapshots beyond the most recent 10.

## Generated Output

Hermes writes or refreshes:

- default root `SOUL.md`, default memory, default config, and default `.env`
- `profiles/researcher`
- `profiles/writer`
- `profiles/builder`
- optional custom Profiles
- shared Wiki files at `WIKI_PATH`

If `profiles/coordinator` already exists, it is kept as a legacy backup/template and is not used as the routine Hermes routing target.

OpenClaw writes a non-invasive package under:

```text
$HOME/.openclaw/opc-team
```

Important OpenClaw files:

- `openclaw.config.patch.json5`
- `agents.json`
- `agent-skill-map.json`
- `agent-dirs/*/`
- `workspaces/*/`
- `discord-channel-routing.json`
- `OPENCLAW_IMPORT.md`

The initializer does not mutate `~/.openclaw/openclaw.json`; review and merge the generated patch yourself or through OpenClaw's config workflow.

## Validation

```bash
python3 -m py_compile \
  "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  "$HOME/.codex/skills/opc-team-init/scripts/init_hermes_opc_team.py"
```

Skill validation:

```bash
python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  "$HOME/.codex/skills/opc-team-init"
```

If your default Python lacks `yaml`, run `quick_validate.py` from a Python environment with PyYAML installed.

## Version

Current skill metadata version: `0.4.0`.
