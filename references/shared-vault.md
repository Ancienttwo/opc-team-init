# Shared Vault Selection

Use this reference when the user initializes or refreshes the shared Wiki memory location.

## Interaction

Default the shared vault to `~/Documents/vault`. Ask the user where the shared vault should live only when they want a different location. Keep the question about location only; do not mix it with custom agent design.

Recommended prompt:

```text
共享 Wiki 放在哪个 vault？你可以给一个 Obsidian vault 根目录，或者让我用当前默认 vault。
```

Current default:

```text
~/Documents/vault
```

## CLI Modes

Interactive selection:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --select-vault
```

Explicit vault root:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --vault-path "$HOME/Documents/vault" \
  --wiki-folder-name "."
```

Exact Wiki directory override:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --wiki-path "$HOME/Documents/vault"
```

## Semantics

- `--vault-path` is the shared vault root.
- `--wiki-folder-name` is a relative directory inside that vault; `.` means use the vault root directly.
- `--wiki-path` bypasses vault selection and sets the final `WIKI_PATH` directly.
- Do not put secrets in the shared vault.
- The same final `WIKI_PATH` must be used by all Hermes Profiles and OpenClaw package files.
