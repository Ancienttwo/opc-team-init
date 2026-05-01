# Custom Peer Profiles

Use this reference when the user wants specialized long-running OPC Agents beyond Hermes default/coordinator-primary, `researcher`, `writer`, and `builder`.

## Interaction Rule

When `$opc-team-init` is activated, ask whether the user wants to add custom peer agents. If yes, collect:

- Profile name.
- User need or mission.
- Responsibilities.
- Boundaries / what it must not do.
- Useful skills or tools, if the user knows them.
- Optional Discord channel name or channel ID.

Do not ask for `parent_profile`; custom agents are peers of the four core agents.

## Spec Shape

Generate one JSON object per custom agent:

```json
{
  "name": "growth-agent",
  "mission": "Own growth experiments, channel strategy, content distribution, and growth retrospectives.",
  "responsibilities": [
    "Turn growth goals into experiments",
    "Track learnings and channel-specific playbooks",
    "Coordinate with writer for content and researcher for evidence"
  ],
  "boundaries": [
    "Do not invent metrics",
    "Do not change product direction without default/coordinator-primary approval"
  ],
  "allowed_skills": ["llm-wiki", "xitter", "blogwatcher", "ideation", "google-workspace", "obsidian"],
  "routing_triggers": ["growth", "distribution", "audience", "funnel", "twitter", "x"],
  "wiki_scope": "Growth plans, experiments, metrics definitions, channel notes, and retrospectives.",
  "discord_channel_name": "#growth-agent",
  "discord_channel_id": ""
}
```

Pass a list of these objects to:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --custom-profile-spec /path/to/custom-profiles.json
```

Or pass one object inline:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --custom-profile-json '{"name":"secretary","mission":"Manage briefs, follow-ups, and personal operations.","responsibilities":["Prepare daily briefs"],"boundaries":["Do not expose secrets"],"allowed_skills":["google-workspace","notion","linear","obsidian"],"routing_triggers":["schedule","brief","follow up"],"wiki_scope":"Administrative workflows and follow-up records."}'
```

## Built-In Presets

The initializer includes two example presets:

- `growth-agent`: growth experiments, distribution strategy, audience learning, and growth retrospectives.
- `secretary`: briefs, follow-ups, administrative tracking, meeting preparation, and personal operations.

Use:

```bash
OPC_TEAM_INIT_DIR="${OPC_TEAM_INIT_DIR:-$HOME/.codex/skills/opc-team-init}"
python3 "$OPC_TEAM_INIT_DIR/scripts/init_opc_team.py" \
  --custom-profile-preset growth-agent \
  --custom-profile-preset secretary
```

For OpenClaw, add `--target openclaw`; the same spec generates peer agent files under `~/.openclaw/opc-team`.

## Routing

For Hermes, default/coordinator-primary must route directly to custom agents when the user's request matches their mission or routing triggers. For OpenClaw, the generated coordinator agent owns that routing. Custom agents are not subordinate to the core four.

## Discord

Default policy is one Discord bot token: owned by Hermes default/coordinator-primary for Hermes, and by the generated coordinator agent for OpenClaw. Custom agents are associated with distinct Discord channels by coordinator channel prompts or OpenClaw package channel routing.

If a custom agent has `discord_channel_id`, the Hermes target adds that channel to default's free-response channels and writes a channel prompt that routes messages to the custom Profile. The OpenClaw target writes the same mapping to `discord-channel-routing.json`, `bindings`, and, when `--discord-guild-id` is supplied, `channels.discord.guilds`.

Do not put the Discord bot token in custom agent `.env` files or generated specs.
