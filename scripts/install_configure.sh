#!/bin/sh
set -eu

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILL_DIR="${OPC_TEAM_INIT_DIR:-$CODEX_HOME/skills/opc-team-init}"

if [ ! -f "$SKILL_DIR/scripts/opc_team_setup.py" ]; then
  if [ -n "${OPC_TEAM_INIT_REPO_URL:-}" ]; then
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' EXIT INT HUP TERM
    git clone --depth 1 "$OPC_TEAM_INIT_REPO_URL" "$tmp_dir/opc-team-init"
    exec python3 "$tmp_dir/opc-team-init/scripts/opc_team_setup.py" \
      install-configure \
      --source-dir "$tmp_dir/opc-team-init" \
      "$@"
  fi
  echo "opc-team-init is not installed at $SKILL_DIR" >&2
  echo "Set OPC_TEAM_INIT_REPO_URL for fsSL bootstrap install, or install the skill first." >&2
  exit 1
fi

exec python3 "$SKILL_DIR/scripts/opc_team_setup.py" install-configure "$@"
