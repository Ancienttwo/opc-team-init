# Team Config Schema

Use this reference when converting a user's natural-language OPC team request into a reusable setup spec for `scripts/opc_team_setup.py`.

## Entry Points

Preferred installed-skill path:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/opc_team_setup.py" configure \
  --team-spec /path/to/opc-team.json
```

Install-or-reuse path:

```bash
python3 "$HOME/.codex/skills/opc-team-init/scripts/opc_team_setup.py" install-configure \
  --team-spec /path/to/opc-team.json
```

fsSL-style bootstrap path:

```bash
curl -fsSL https://raw.githubusercontent.com/Ancienttwo/opc-team-init/main/scripts/install_configure.sh \
  | OPC_TEAM_INIT_REPO_URL=https://github.com/Ancienttwo/opc-team-init.git \
    bash -s -- --team-spec /path/to/opc-team.json
```

The shell wrapper is only a bootstrapper. All profile/config writes still go through `init_opc_team.py`.

## JSON Shape

```json
{
  "target": "hermes",
  "language": "zh-CN",
  "vault_path": "~/Documents/vault",
  "dependency_mode": "prompt",
  "discord": {
    "user_id": "",
    "guild_id": "",
    "home_channel": {
      "name": "#agent-proposals",
      "id": ""
    }
  },
  "agents": [
    {
      "name": "Orchestrator",
      "profile": "default",
      "channel": {"name": "#agent-proposals", "id": ""}
    },
    {
      "name": "Researcher",
      "profile": "researcher",
      "channel": {"name": "#researcher", "id": ""}
    },
    {
      "name": "Writer",
      "profile": "writer",
      "channel": {"name": "#writer", "id": ""}
    },
    {
      "name": "Builder",
      "profile": "builder",
      "channel": {"name": "#builder", "id": ""}
    },
    {
      "name": "Secretary",
      "profile": "secretary",
      "mission": "Manage briefs, follow-ups, meeting preparation, and personal operations.",
      "responsibilities": ["Prepare concise briefs", "Track follow-ups and waiting items"],
      "boundaries": ["Do not expose secrets", "Do not send external messages without approval"],
      "routing_triggers": ["secretary", "brief", "follow-up", "meeting", "schedule"],
      "channel": {"name": "#secretary", "id": ""}
    }
  ]
}
```

## Semantics

- `target`: `hermes` or `openclaw`. Default is `hermes`.
- `language`: `en`, `zh-CN`, or `zh-TW`. Default setup-script language is `zh-CN`; `init_opc_team.py` still requires an explicit language.
- `vault_path`: Obsidian/shared Wiki vault root. Use `wiki_path` only when the final `WIKI_PATH` should not equal the vault root.
- `dependency_mode`: `prompt`, `strict`, or `off`. Dependencies are detected and reported, not installed.
- `agents[]`: core agents are always supported. Extra agent names become custom peer Profiles.
- `channels[]`: optional override list. Each entry can use `agent`, `profile`, `name`/`channel_name`, and `id`/`channel_id`.
- `discord.user_id`, `discord.guild_id`: written only when supplied. Bot tokens are never read from files; pass `--discord-bot-token` explicitly if needed.

## Channel Policy

- `default`, `coordinator`, `coordinator-primary`, and `orchestrator` all resolve to the Hermes default/coordinator-primary entrypoint.
- The default/coordinator home channel is the only free-response channel. It is suitable for the Orchestrator to talk freely.
- Researcher, writer, builder, and custom agent channels get `discord.channel_profiles` for runtime routing plus `discord.channel_prompts` for compatible prompt/context injection. They keep `require_mention: true` and `auto_thread: true`, so new channel work needs a mention and opens a thread.
- The durable source of truth for generated channel routing is `OPC_CHANNELS.json`.

## Built-In Custom Examples

- `growth-agent`: growth experiments, distribution strategy, audience learning, and growth retrospectives.
- `secretary`: briefs, follow-ups, administrative tracking, meeting preparation, and personal operations.

These are peer Profiles. They are not children of researcher, writer, or builder.
