# GStack/GBrain Skill Distribution

Use this reference when changing which skills belong to each OPC Agent.

## Rules

- Use role-specific skill sets, not "everything everywhere".
- Hermes: default/coordinator-primary owns GBrain always-on and brain-first behavior. OpenClaw: the generated `coordinator` agent owns it.
- Specialist agents only receive task-specific GBrain skills.
- Do not vendor GStack or GBrain into this skill.

## Hermes Matrix

| Agent | GStack skills | GBrain skills |
|---|---|---|
| `default` / `coordinator-primary` | `office-hours`, `autoplan`, `plan-ceo-review`, `plan-eng-review`, `plan-design-review`, `plan-devex-review`, `retro`, `checkpoint`, `context-save`, `context-restore`, `learn`, `setup-gbrain` | `brain-ops`, `signal-detector`, `query`, `reports`, `daily-task-manager`, `cron-scheduler`, `minion-orchestrator`, `maintain`, `skillpack-check` |
| `researcher` | `investigate`, `browse`, `scrape`, `benchmark-models` | `query`, `data-research`, `ingest`, `idea-ingest`, `media-ingest`, `meeting-ingestion`, `enrich`, `citation-fixer` |
| `writer` | `office-hours`, `design-consultation`, `document-release`, `make-pdf` | `query`, `reports`, `publish`, `briefing` |
| `builder` | `investigate`, `review`, `qa`, `qa-only`, `cso`, `health`, `ship`, `land-and-deploy`, `setup-deploy`, `benchmark`, `canary`, `careful`, `guard`, `freeze`, `unfreeze`, `devex-review`, `design-review`, `browse` | `query`, `testing`, `cross-modal-review` |
| `growth-agent` | `office-hours`, `plan-ceo-review`, `plan-devex-review`, `design-consultation`, `browse`, `scrape`, `document-release`, `retro` | `query`, `idea-ingest`, `media-ingest`, `data-research`, `reports`, `enrich` |
| `secretary` | `office-hours`, `document-release`, `make-pdf`, `learn` | `briefing`, `daily-task-prep`, `daily-task-manager`, `meeting-ingestion`, `reports`, `query`, `cron-scheduler`, `ingest` |

## OpenClaw Matrix

OpenClaw uses native OpenClaw skill IDs, not Hermes/GStack skill names.

| Agent | GStack OpenClaw skills | GBrain OpenClaw skills |
|---|---|---|
| `coordinator` | `gstack-openclaw-office-hours`, `gstack-openclaw-ceo-review`, `gstack-openclaw-retro` | `query`, `maintain`, `setup` |
| `researcher` | `gstack-openclaw-investigate` | `query`, `ingest`, `enrich` |
| `writer` | `gstack-openclaw-office-hours` | `query`, `briefing` |
| `builder` | `gstack-openclaw-investigate` | `query` |
| `growth-agent` | `gstack-openclaw-office-hours`, `gstack-openclaw-ceo-review`, `gstack-openclaw-retro` | `query`, `ingest`, `enrich` |
| `secretary` | `gstack-openclaw-office-hours` | `query`, `briefing`, `ingest` |

## Generated Outputs

- Hermes target: selected skills are kept enabled by role in `skills.disabled`.
- OpenClaw target: selected skills are written into `agents.list[].skills`, `skills.entries`, `agent-skill-map.json`, and `agents.json`.
