# GStack and GBrain Dependencies

Use this reference when changing dependency detection, install guidance, or role-skill distribution.

## Policy

GStack and GBrain are external MIT dependencies. The initializer detects them and prints install guidance, but it must not clone, vendor, or install them automatically.

## CLI

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --dependency-mode prompt
```

Modes:

- `prompt`: default; print missing dependency instructions and continue.
- `strict`: fail if a required dependency root is missing.
- `off`: skip missing dependency warnings.

Root overrides:

```bash
--gstack-root "$HOME/gstack"
--gbrain-root "$HOME/gbrain"
```

## Install Hints

GStack for Hermes:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host hermes
```

GBrain for agents:

```text
https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md
```

Standalone GBrain:

```bash
git clone https://github.com/garrytan/gbrain.git ~/gbrain && cd ~/gbrain && bun install && bun link
```

## Hermes Behavior

- GStack skills are expected under `~/.hermes/skills/gstack*` after GStack setup.
- GBrain skills are loaded via `skills.external_dirs` pointing at `~/gbrain/skills` when detected.
- `skills.disabled` is computed from profile skills, global Hermes skills, and configured external dirs.

## OpenClaw Behavior

OpenClaw package generation writes:

- `dependencies.json`
- `agent-skill-map.json`
- per-agent `gstack_skills`, `gbrain_skills`, and `dependency_notes` in `agents.json`
