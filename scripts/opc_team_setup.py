#!/usr/bin/env python3
"""Install and configure the OPC team skill from a reusable team spec."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


CORE_PROFILES = {"default", "researcher", "writer", "builder"}
DEFAULT_LANGUAGE = "zh-CN"
DEFAULT_TARGET = "hermes"
DEFAULT_DEPENDENCY_MODE = "prompt"
DEFAULT_VAULT = Path.home() / "Documents" / "vault"

PROFILE_ALIASES = {
    "orchestrator": "default",
    "coordinator": "default",
    "coordinator-primary": "default",
    "default": "default",
    "researcher": "researcher",
    "writer": "writer",
    "builder": "builder",
}

PRESET_CUSTOM_AGENTS: dict[str, dict[str, Any]] = {
    "growth-agent": {
        "mission": "Own growth experiments, distribution strategy, audience learning, and growth retrospectives for the user.",
        "responsibilities": [
            "Turn growth goals into concrete experiments and review loops",
            "Track channel-specific playbooks and growth learnings",
            "Coordinate with writer for content assets and researcher for evidence",
        ],
        "boundaries": [
            "Do not invent metrics, audience feedback, or conversion data",
            "Do not change product direction without default/coordinator-primary approval",
            "Do not publish externally without explicit user approval",
        ],
        "routing_triggers": ["growth", "distribution", "audience", "funnel", "twitter", "x"],
        "wiki_scope": "Growth plans, experiments, metrics definitions, channel notes, content distribution playbooks, and retrospectives.",
    },
    "secretary": {
        "mission": "Manage briefs, follow-ups, administrative tracking, meeting preparation, and personal operations for the user.",
        "responsibilities": [
            "Prepare concise daily or project briefs",
            "Track follow-ups, waiting items, and administrative loose ends",
            "Coordinate with default/coordinator-primary when work needs routing",
        ],
        "boundaries": [
            "Do not expose secrets or private contact details in Wiki pages",
            "Do not send messages or schedule externally without explicit approval",
            "Do not make business decisions on the user's behalf",
        ],
        "routing_triggers": ["secretary", "brief", "follow-up", "meeting", "schedule", "admin"],
        "wiki_scope": "Briefs, follow-ups, meeting prep, administrative workflows, and user operations notes.",
    },
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def default_skill_dir() -> Path:
    return Path(os.environ.get("OPC_TEAM_INIT_DIR", codex_home() / "skills" / "opc-team-init")).expanduser()


def current_source_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    return json.loads(path.expanduser().read_text(encoding="utf-8"))


def canonical_profile(value: str) -> str:
    name = str(value or "").strip().lower().replace("_", "-")
    if not name:
        raise SystemExit("Agent/profile name must not be empty")
    return PROFILE_ALIASES.get(name, name)


def channel_id_from(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("id") or value.get("channel_id") or "").strip()
    return str(value or "").strip()


def channel_name_from(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("channel_name") or fallback).strip()
    return fallback


def agent_profile(agent: dict[str, Any]) -> str:
    raw = agent.get("profile") or agent.get("role") or agent.get("name")
    return canonical_profile(str(raw))


def channel_records(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}

    def put(profile: str, channel_id: str, channel_name: str) -> None:
        if not channel_id:
            return
        profile = canonical_profile(profile)
        records[profile] = {
            "profile": profile,
            "channel_id": channel_id,
            "channel_name": channel_name or f"#{profile}",
        }

    discord = spec.get("discord") if isinstance(spec.get("discord"), dict) else {}
    home_id = channel_id_from(discord.get("home_channel") or discord.get("channel_id"))
    if home_id:
        put("default", home_id, channel_name_from(discord.get("home_channel"), "#agent-proposals"))

    for channel in spec.get("channels") or []:
        if not isinstance(channel, dict):
            raise SystemExit("Each channels[] entry must be an object")
        profile = channel.get("profile") or channel.get("agent") or channel.get("name")
        put(
            str(profile),
            channel_id_from(channel),
            str(channel.get("channel_name") or channel.get("name") or f"#{canonical_profile(str(profile))}").strip(),
        )

    for agent in spec.get("agents") or []:
        if not isinstance(agent, dict):
            raise SystemExit("Each agents[] entry must be an object")
        profile = agent_profile(agent)
        channel_value = agent.get("channel") or agent.get("discord_channel")
        channel_id = channel_id_from(channel_value) or str(agent.get("channel_id") or agent.get("discord_channel_id") or "").strip()
        channel_name = channel_name_from(channel_value, str(agent.get("channel_name") or agent.get("discord_channel_name") or f"#{profile}"))
        put(profile, channel_id, channel_name)

    return records


def custom_agent_specs(spec: dict[str, Any], channels: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    custom: dict[str, dict[str, Any]] = {}
    for agent in spec.get("agents") or []:
        if not isinstance(agent, dict):
            raise SystemExit("Each agents[] entry must be an object")
        profile = agent_profile(agent)
        if profile in CORE_PROFILES:
            continue
        preset = PRESET_CUSTOM_AGENTS.get(profile, {})
        mission = str(agent.get("mission") or agent.get("description") or preset.get("mission") or f"Own specialized work for {profile}.").strip()
        responsibilities = agent.get("responsibilities") or agent.get("duties") or preset.get("responsibilities") or [f"Own specialized work for: {mission}"]
        boundaries = agent.get("boundaries") or preset.get("boundaries") or [
            "Do not write secrets into memory, Wiki, or config files",
            "Do not make external commitments without explicit user approval",
            "Do not bypass default/coordinator-primary routing for cross-profile work",
        ]
        triggers = agent.get("routing_triggers") or agent.get("triggers") or preset.get("routing_triggers") or [profile.replace("-", " "), profile]
        channel = channels.get(profile, {})
        custom[profile] = {
            "name": profile,
            "mission": mission,
            "responsibilities": responsibilities,
            "boundaries": boundaries,
            "allowed_skills": agent.get("allowed_skills") or [],
            "openclaw_skills": agent.get("openclaw_skills") or [],
            "routing_triggers": triggers,
            "wiki_scope": str(agent.get("wiki_scope") or preset.get("wiki_scope") or "Specialized work records, decisions, handoffs, and reusable methods.").strip(),
            "discord_channel_name": channel.get("channel_name") or str(agent.get("discord_channel_name") or f"#{profile}"),
            "discord_channel_id": channel.get("channel_id") or str(agent.get("discord_channel_id") or ""),
            "allow_all_skills": bool(agent.get("allow_all_skills", False)),
        }
    return [custom[name] for name in sorted(custom)]


def interactive_spec() -> dict[str, Any]:
    print("OPC team setup interactive mode. Press Enter to accept defaults.")
    target = input(f"Target [{DEFAULT_TARGET}]: ").strip() or DEFAULT_TARGET
    language = input(f"Language [{DEFAULT_LANGUAGE}]: ").strip() or DEFAULT_LANGUAGE
    vault = input(f"Shared vault [{DEFAULT_VAULT}]: ").strip() or str(DEFAULT_VAULT)
    agents = [
        {"name": "Orchestrator", "profile": "default", "channel": {"name": "#agent-proposals", "id": input("Orchestrator home channel ID [blank to skip Discord]: ").strip()}},
        {"name": "Researcher", "profile": "researcher", "channel": {"name": "#researcher", "id": input("Researcher channel ID [blank to skip]: ").strip()}},
        {"name": "Writer", "profile": "writer", "channel": {"name": "#writer", "id": input("Writer channel ID [blank to skip]: ").strip()}},
        {"name": "Builder", "profile": "builder", "channel": {"name": "#builder", "id": input("Builder channel ID [blank to skip]: ").strip()}},
    ]
    add_secretary = (input("Add secretary profile? [Y/n]: ").strip().lower() or "y") != "n"
    if add_secretary:
        agents.append({"name": "Secretary", "profile": "secretary", "channel": {"name": "#secretary", "id": input("Secretary channel ID [blank to skip]: ").strip()}})
    return {
        "target": target,
        "language": language,
        "vault_path": vault,
        "dependency_mode": DEFAULT_DEPENDENCY_MODE,
        "agents": agents,
    }


def load_team_spec(path: Path | None) -> dict[str, Any]:
    if path is None:
        return interactive_spec()
    data = load_json(path)
    if not isinstance(data, dict):
        raise SystemExit("Team spec must be a JSON object")
    return data


def init_script(skill_dir: Path) -> Path:
    path = skill_dir / "scripts" / "init_opc_team.py"
    if not path.exists():
        raise SystemExit(f"Initializer not found: {path}")
    return path


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, text=True, check=check)


def run_audit(args: argparse.Namespace, skill_dir: Path, spec: dict[str, Any]) -> None:
    if args.skip_audit or str(spec.get("target") or DEFAULT_TARGET).lower() != "hermes":
        return
    hermes_home = Path(spec.get("hermes_home") or args.hermes_home).expanduser()
    proc = run(
        [sys.executable, str(init_script(skill_dir)), "--mode", "audit", "--hermes-home", str(hermes_home)],
        check=False,
    )
    if proc.returncode == 2 and not args.allow_severe_audit:
        raise SystemExit("Audit found severe gateway risk. Re-run with --allow-severe-audit only after resolving or accepting it.")


def configure_command(args: argparse.Namespace, skill_dir: Path, spec: dict[str, Any]) -> tuple[list[str], list[Path]]:
    target = str(spec.get("target") or DEFAULT_TARGET).lower()
    language = str(spec.get("language") or DEFAULT_LANGUAGE)
    dependency_mode = str(spec.get("dependency_mode") or DEFAULT_DEPENDENCY_MODE)
    channels = channel_records(spec)
    custom_specs = custom_agent_specs(spec, channels)

    cmd = [
        sys.executable,
        str(init_script(skill_dir)),
        "--target",
        target,
        "--language",
        language,
        "--dependency-mode",
        dependency_mode,
    ]

    hermes_home = Path(spec.get("hermes_home") or args.hermes_home).expanduser()
    openclaw_home = Path(spec.get("openclaw_home") or args.openclaw_home).expanduser()
    cmd.extend(["--hermes-home", str(hermes_home), "--openclaw-home", str(openclaw_home)])

    if spec.get("wiki_path"):
        cmd.extend(["--wiki-path", str(Path(spec["wiki_path"]).expanduser())])
    else:
        vault = Path(spec.get("vault_path") or DEFAULT_VAULT).expanduser()
        cmd.extend(["--vault-path", str(vault)])
        if spec.get("wiki_folder_name"):
            cmd.extend(["--wiki-folder-name", str(spec["wiki_folder_name"])])

    discord = spec.get("discord") if isinstance(spec.get("discord"), dict) else {}
    if discord.get("guild_id"):
        cmd.extend(["--discord-guild-id", str(discord["guild_id"])])
    if discord.get("user_id"):
        cmd.extend(["--discord-user-id", str(discord["user_id"])])
    if args.discord_bot_token:
        cmd.extend(["--discord-bot-token", args.discord_bot_token])

    if "default" in channels:
        cmd.extend(["--discord-channel-id", channels["default"]["channel_id"]])

    for profile, channel in sorted(channels.items()):
        cmd.extend(["--agent-channel", f"{profile}={channel['channel_id']}"])
        cmd.extend(["--agent-channel-name", f"{profile}={channel['channel_name']}"])

    temp_files: list[Path] = []
    if custom_specs:
        fd, path_s = tempfile.mkstemp(prefix="opc-custom-profiles-", suffix=".json")
        path = Path(path_s)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(custom_specs, f, ensure_ascii=False, indent=2)
            f.write("\n")
        temp_files.append(path)
        cmd.extend(["--custom-profile-spec", str(path)])

    if args.force_wiki:
        cmd.append("--force-wiki")
    if args.no_copy_auth:
        cmd.append("--no-copy-auth")
    if args.start_gateway:
        cmd.append("--start-gateway")
    if args.run_chat_checks:
        cmd.append("--run-chat-checks")
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd, temp_files


def configure(args: argparse.Namespace, skill_dir: Path) -> int:
    spec = load_team_spec(args.team_spec)
    run_audit(args, skill_dir, spec)
    cmd, temp_files = configure_command(args, skill_dir, spec)
    try:
        run(cmd, check=True)
    finally:
        for path in temp_files:
            path.unlink(missing_ok=True)
    return 0


def copy_ignore(_src: str, names: list[str]) -> set[str]:
    ignored = {".git", ".claude", "__pycache__", ".pytest_cache"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def install_skill(args: argparse.Namespace) -> Path:
    source = Path(args.source_dir or current_source_dir()).expanduser().resolve()
    dest = Path(args.skill_dir or default_skill_dir()).expanduser()
    if source == dest.resolve():
        return dest
    if dest.exists() and not args.update_existing:
        init_script(dest)
        print(f"using existing skill: {dest}")
        return dest
    if args.dry_run:
        action = "update" if dest.exists() else "install"
        print(f"dry-run: would {action} {source} -> {dest}")
        return dest
    if dest.exists():
        backup_root = dest.parent / ".opc-team-init-backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        backup = backup_root / _dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        shutil.move(str(dest), str(backup))
        print(f"backup: moved existing skill to {backup}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest, ignore=copy_ignore)
    print(f"installed skill: {dest}")
    return dest


def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--team-spec", type=Path, help="JSON team spec. If omitted, run an interactive prompt.")
    parser.add_argument("--skill-dir", type=Path, help="Installed opc-team-init skill directory.")
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--openclaw-home", type=Path, default=Path.home() / ".openclaw")
    parser.add_argument("--discord-bot-token", help="Optional real Discord bot token. Not read from files.")
    parser.add_argument("--skip-audit", action="store_true", help="Skip audit-first check for Hermes target.")
    parser.add_argument("--allow-severe-audit", action="store_true", help="Continue even if audit reports severe gateway risk.")
    parser.add_argument("--force-wiki", action="store_true")
    parser.add_argument("--no-copy-auth", action="store_true")
    parser.add_argument("--start-gateway", action="store_true")
    parser.add_argument("--run-chat-checks", action="store_true")
    parser.add_argument("--dry-run", action="store_true")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    configure_parser = sub.add_parser("configure", help="Configure an installed OPC team skill.")
    add_common_flags(configure_parser)

    install_parser = sub.add_parser("install-configure", help="Install or reuse the skill, then configure it.")
    add_common_flags(install_parser)
    install_parser.add_argument("--source-dir", type=Path, help="Source skill directory to install from.")
    install_parser.add_argument("--update-existing", action="store_true", help="Back up and replace an existing installed skill.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "configure":
        skill_dir = Path(args.skill_dir or default_skill_dir()).expanduser()
        return configure(args, skill_dir)
    if args.command == "install-configure":
        skill_dir = install_skill(args)
        return configure(args, skill_dir)
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
