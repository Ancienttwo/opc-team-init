# OPC Team Init

Initialize or refresh an OPC-style multi-agent team for Hermes or OpenClaw.

The default team is:

- default Hermes agent as `coordinator-primary`: goals, routing, synthesis, archive
- `researcher`: evidence, verification, uncertainty
- `writer`: structure, reader-facing content
- `builder`: implementation, debugging, tests

Only the coordinator role is implemented by rewriting/augmenting the user's default Hermes agent. All other Hermes roles, including custom agents, are created as real Profiles.

It also supports user-defined peer agents such as `growth-agent` and `secretary`, shared Wiki memory, Discord proposal intake, and temporary Subagent reporting rules.

## Install

Install this folder as a Codex skill under:

```bash
$HOME/.codex/skills/opc-team-init
```

The skill is MIT licensed. See [LICENSE](LICENSE).

## Quick Start

Hermes target:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py"
```

OpenClaw target:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --target openclaw
```

The default shared Wiki path is:

```text
$HOME/Documents/vault
```

Choose a vault interactively:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --select-vault
```

Use an exact Wiki directory:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --wiki-path "/absolute/path/to/vault"
```

## Custom Agents

Add built-in custom peer agents:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

Add your own custom agent from JSON:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
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
  --dependency-mode prompt
```

Use `--dependency-mode strict` in CI-style checks.

## Discord

The Hermes default policy is one Discord bot token owned by the default/coordinator-primary agent.

Hermes proposal channel:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

OpenClaw channel routing:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/init_opc_team.py" \
  --target openclaw \
  --discord-guild-id 345678901234567890 \
  --discord-channel-id 123456789012345678 \
  --discord-user-id 234567890123456789
```

Do not commit real bot tokens.

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

Current skill metadata version: `0.3.0`.
