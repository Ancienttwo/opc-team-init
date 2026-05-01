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

GStack for OpenClaw:

```bash
git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host openclaw
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
- Hermes config must keep `platform_toolsets.cli += delegation`, but must not write deprecated `delegation.default_toolsets`.

## OpenClaw Behavior

OpenClaw dependency detection checks:

- GStack installed skills under `~/.openclaw/skills/gstack`.
- GStack source skills under `~/gstack/openclaw/skills`.
- GBrain skill folders under `~/gbrain/skills`.
- GBrain OpenClaw plugin metadata at `~/gbrain/openclaw.plugin.json`.

OpenClaw package generation writes:

- `dependencies.json`
- `agent-skill-map.json`
- per-agent `gstack_skills`, `gbrain_skills`, and `dependency_notes` in `agents.json`
- `openclaw.config.patch.json5` with `skills.load.extraDirs` for detected external skill dirs
- optional `plugins.load.paths` for a detected GBrain OpenClaw plugin

If the GStack repo exists but the OpenClaw host install does not, prefer `~/gstack/openclaw/skills` in the generated `skills.load.extraDirs` and still print `./setup --host openclaw` as the host-install next step.
