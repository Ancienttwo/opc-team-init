# OpenClaw Target

Use this reference when the user asks for OpenClaw support.

> The OpenClaw target also takes `--language en|zh-CN|zh-TW`. The chosen language is recorded in `manifest.json` and used for every prompt, role-memory seed, channel routing prompt, routing table, and Wiki seed page in the generated package. English is the source of truth.

## Policy

This skill treats OpenClaw as a configuration-package target, not as an in-place config editor. The initializer must not mutate `.openclaw/openclaw.json`; it generates package files plus an `openclaw.config.patch.json5` fragment that the user can review and merge.

## Command

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language en \
  --target openclaw
```

With custom agents:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --language zh-CN \
  --target openclaw \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

## Output

The OpenClaw target writes a non-secret package under:

```text
~/.openclaw/opc-team
```

Expected files:

- `manifest.json`: package metadata and compatibility mode.
- `dependencies.json`: detected GStack/GBrain dependency state and install hints.
- `agent-skill-map.json`: role-based OpenClaw skill distribution matrix.
- `agents.json`: structured registry for core and custom peer agents.
- `agents/*.md`: prompt and role-memory seeds.
- `agent-dirs/*/`: real per-agent `agentDir` folders referenced by the config patch.
- `workspaces/*/`: real per-agent `workspace` folders referenced by the config patch.
- `openclaw.config.patch.json5`: mergeable config fragment with `agents.list`, `skills.load.extraDirs`, `skills.entries`, optional `plugins.load.paths`, optional `bindings`, and optional `channels.discord`.
- `custom-profiles.json`: custom peer agent registry.
- `routing-table.md`: coordinator routing rules.
- `discord-channel-routing.json`: single-token, multi-channel routing policy.
- `subagent-reporting.md`: temporary Subagent report contract.
- `.env.example`: placeholders only, no secrets.
- `OPENCLAW_IMPORT.md`: manual integration notes.
- `wiki-template/`: minimal shared Wiki seed pages.

## Discord

Default to one coordinator-owned Discord token. Custom agents may have distinct channels, but the generated specs must not contain real tokens.

When channel IDs are supplied, the package writes route bindings:

- `bindings[].agentId`
- `bindings[].match.channel: "discord"`
- `bindings[].match.peer.kind: "channel"`
- `bindings[].match.peer.id`

When `--discord-guild-id` is also supplied, the config patch adds `channels.discord.guilds.<guildId>.channels.<channelId>` entries with channel-specific `systemPrompt` and role-appropriate `skills`.

## Skills

Do not reuse Hermes skill IDs for OpenClaw. Use the OpenClaw-native GStack IDs:

- `gstack-openclaw-office-hours`
- `gstack-openclaw-ceo-review`
- `gstack-openclaw-investigate`
- `gstack-openclaw-retro`

Use only the GBrain OpenClaw plugin skill IDs that the plugin declares: `ingest`, `query`, `maintain`, `enrich`, `briefing`, `migrate`, and `setup`.

The OpenClaw target writes these into `agents.list[].skills`, `skills.entries`, `agent-skill-map.json`, and `agents.json`.

## Subagents

OpenClaw support uses the same Subagent model as Hermes at the prompt/protocol level: spawned temporary agents report only to their owning core or custom agent. The package records this in `agents.json` as `subagent_report_target`.
