# GStack/GBrain Skill Distribution

Use this reference when changing which skills belong to each OPC Agent.

## Rules

- Use role-specific skill sets, not "everything everywhere".
- `coordinator` owns GBrain always-on and brain-first behavior.
- Specialist agents only receive task-specific GBrain skills.
- Do not vendor GStack or GBrain into this skill.

## Matrix

| Agent | GStack skills | GBrain skills |
|---|---|---|
| `coordinator` | `office-hours`, `autoplan`, `plan-ceo-review`, `plan-eng-review`, `plan-design-review`, `plan-devex-review`, `retro`, `checkpoint`, `context-save`, `context-restore`, `learn`, `setup-gbrain` | `brain-ops`, `signal-detector`, `query`, `reports`, `daily-task-manager`, `cron-scheduler`, `minion-orchestrator`, `maintain`, `skillpack-check` |
| `researcher` | `investigate`, `browse`, `scrape`, `benchmark-models` | `query`, `data-research`, `ingest`, `idea-ingest`, `media-ingest`, `meeting-ingestion`, `enrich`, `citation-fixer` |
| `writer` | `office-hours`, `design-consultation`, `document-release`, `make-pdf` | `query`, `reports`, `publish`, `briefing` |
| `builder` | `investigate`, `review`, `qa`, `qa-only`, `cso`, `health`, `ship`, `land-and-deploy`, `setup-deploy`, `benchmark`, `canary`, `careful`, `guard`, `freeze`, `unfreeze`, `devex-review`, `design-review`, `browse` | `query`, `testing`, `cross-modal-review` |
| `growth-agent` | `office-hours`, `plan-ceo-review`, `plan-devex-review`, `design-consultation`, `browse`, `scrape`, `document-release`, `retro` | `query`, `idea-ingest`, `media-ingest`, `data-research`, `reports`, `enrich` |
| `secretary` | `office-hours`, `document-release`, `make-pdf`, `learn` | `briefing`, `daily-task-prep`, `daily-task-manager`, `meeting-ingestion`, `reports`, `query`, `cron-scheduler`, `ingest` |

## Generated Outputs

- Hermes target: selected skills are kept enabled by role in `skills.disabled`.
- OpenClaw target: selected skills are written into `agent-skill-map.json` and `agents.json`.
