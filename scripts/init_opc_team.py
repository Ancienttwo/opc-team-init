#!/usr/bin/env python3
"""Initialize or refresh an OPC agent team for Hermes or OpenClaw."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import textwrap
from typing import Any


PROFILES = ("coordinator", "researcher", "writer", "builder")
HERMES_SPECIALIST_PROFILES = ("researcher", "writer", "builder")
RESERVED_CUSTOM_PROFILE_NAMES = set(PROFILES) | {"default"}
PLACEHOLDER_CHANNEL = "<AGENT_PROPOSALS_CHANNEL_ID>"
CUSTOM_REGISTRY_NAME = "OPC_CUSTOM_PROFILES.json"
ROUTING_TABLE_NAME = "OPC_ROUTING_TABLE.md"
OPENCLAW_PACKAGE_DIRNAME = "opc-team"
DEFAULT_WIKI_FOLDER_NAME = "."
PROFILE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

CORE_PROFILE_SUMMARY = {
    "coordinator": "目标定义、任务拆解、路由、汇总、归档；不直接研究、写稿、写代码。",
    "researcher": "查证、交叉验证、标注不确定性；不写最终稿。",
    "writer": "结构、表达、面向读者的内容产出；不重新做事实研究。",
    "builder": "代码、页面、系统实现、调试、测试；不负责叙事和方向判断。",
}

ALLOWED_SKILLS = {
    "coordinator": {
        "hermes-agent",
        "llm-wiki",
        "plan",
        "writing-plans",
        "subagent-driven-development",
        "requesting-code-review",
        "obsidian",
        "notion",
        "google-workspace",
        "linear",
        "webhook-subscriptions",
        "github-issues",
        "dogfood",
    },
    "researcher": {
        "llm-wiki",
        "arxiv",
        "blogwatcher",
        "xitter",
        "research-paper-writing",
        "polymarket",
        "obsidian",
        "google-workspace",
        "nano-pdf",
        "ocr-and-documents",
        "youtube-content",
        "huggingface-hub",
        "jupyter-live-kernel",
        "subagent-driven-development",
    },
    "writer": {
        "llm-wiki",
        "obsidian",
        "research-paper-writing",
        "ideation",
        "google-workspace",
        "notion",
        "powerpoint",
        "nano-pdf",
        "ocr-and-documents",
        "youtube-content",
        "ascii-art",
        "architecture-diagram",
        "excalidraw",
        "subagent-driven-development",
    },
    "builder": {
        "hermes-agent",
        "codebase-inspection",
        "test-driven-development",
        "systematic-debugging",
        "github-auth",
        "github-code-review",
        "github-issues",
        "github-pr-workflow",
        "github-repo-management",
        "requesting-code-review",
        "subagent-driven-development",
        "codex",
        "claude-code",
        "opencode",
        "plan",
        "writing-plans",
        "native-mcp",
        "mcporter",
        "webhook-subscriptions",
        "dogfood",
    },
}

GSTACK_HERMES_INSTALL_COMMAND = "git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host hermes"
GSTACK_OPENCLAW_INSTALL_COMMAND = "git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/gstack && cd ~/gstack && ./setup --host openclaw"
GBRAIN_AGENT_INSTALL_URL = "https://raw.githubusercontent.com/garrytan/gbrain/master/INSTALL_FOR_AGENTS.md"
GBRAIN_STANDALONE_INSTALL_COMMAND = "git clone https://github.com/garrytan/gbrain.git ~/gbrain && cd ~/gbrain && bun install && bun link"

GSTACK_SKILLS_BY_AGENT = {
    "coordinator": {
        "office-hours",
        "autoplan",
        "plan-ceo-review",
        "plan-eng-review",
        "plan-design-review",
        "plan-devex-review",
        "retro",
        "checkpoint",
        "context-save",
        "context-restore",
        "learn",
        "setup-gbrain",
    },
    "researcher": {"investigate", "browse", "scrape", "benchmark-models"},
    "writer": {"office-hours", "design-consultation", "document-release", "make-pdf"},
    "builder": {
        "investigate",
        "review",
        "qa",
        "qa-only",
        "cso",
        "health",
        "ship",
        "land-and-deploy",
        "setup-deploy",
        "benchmark",
        "canary",
        "careful",
        "guard",
        "freeze",
        "unfreeze",
        "devex-review",
        "design-review",
        "browse",
    },
    "growth-agent": {
        "office-hours",
        "plan-ceo-review",
        "plan-devex-review",
        "design-consultation",
        "browse",
        "scrape",
        "document-release",
        "retro",
    },
    "secretary": {"office-hours", "document-release", "make-pdf", "learn"},
}

GBRAIN_SKILLS_BY_AGENT = {
    "coordinator": {
        "brain-ops",
        "signal-detector",
        "query",
        "reports",
        "daily-task-manager",
        "cron-scheduler",
        "minion-orchestrator",
        "maintain",
        "skillpack-check",
    },
    "researcher": {
        "query",
        "data-research",
        "ingest",
        "idea-ingest",
        "media-ingest",
        "meeting-ingestion",
        "enrich",
        "citation-fixer",
    },
    "writer": {"query", "reports", "publish", "briefing"},
    "builder": {"query", "testing", "cross-modal-review"},
    "growth-agent": {"query", "idea-ingest", "media-ingest", "data-research", "reports", "enrich"},
    "secretary": {
        "briefing",
        "daily-task-prep",
        "daily-task-manager",
        "meeting-ingestion",
        "reports",
        "query",
        "cron-scheduler",
        "ingest",
    },
}

OPENCLAW_GSTACK_SKILLS_BY_AGENT = {
    "coordinator": {
        "gstack-openclaw-office-hours",
        "gstack-openclaw-ceo-review",
        "gstack-openclaw-retro",
    },
    "researcher": {"gstack-openclaw-investigate"},
    "writer": {"gstack-openclaw-office-hours"},
    "builder": {"gstack-openclaw-investigate"},
    "growth-agent": {
        "gstack-openclaw-office-hours",
        "gstack-openclaw-ceo-review",
        "gstack-openclaw-retro",
    },
    "secretary": {"gstack-openclaw-office-hours"},
}

OPENCLAW_GBRAIN_SKILLS_BY_AGENT = {
    "coordinator": {"query", "maintain", "setup"},
    "researcher": {"query", "ingest", "enrich"},
    "writer": {"query", "briefing"},
    "builder": {"query"},
    "growth-agent": {"query", "ingest", "enrich"},
    "secretary": {"query", "briefing", "ingest"},
}


PRESET_CUSTOM_PROFILES: dict[str, dict[str, Any]] = {
    "growth-agent": {
        "name": "growth-agent",
        "mission": "Own growth experiments, distribution strategy, audience learning, and growth retrospectives for the user.",
        "responsibilities": [
            "Turn growth goals into concrete experiments and review loops",
            "Track channel-specific playbooks, especially X/Twitter-style growth",
            "Coordinate with writer for content assets and researcher for evidence",
            "Keep growth learnings and experiment state in the shared Wiki",
        ],
        "boundaries": [
            "Do not invent metrics, audience feedback, or conversion data",
            "Do not change product direction without default/coordinator-primary approval",
            "Do not publish externally without explicit user approval",
        ],
        "allowed_skills": [
            "llm-wiki",
            "subagent-driven-development",
            "xitter",
            "blogwatcher",
            "ideation",
            "research-paper-writing",
            "google-workspace",
            "obsidian",
        ],
        "routing_triggers": ["growth", "distribution", "audience", "funnel", "twitter", "x", "内容增长"],
        "wiki_scope": "Growth plans, experiments, metrics definitions, channel notes, content distribution playbooks, and retrospectives.",
        "discord_channel_name": "#growth-agent",
        "discord_channel_id": "",
    },
    "secretary": {
        "name": "secretary",
        "mission": "Manage briefs, follow-ups, administrative tracking, meeting preparation, and personal operations for the user.",
        "responsibilities": [
            "Prepare concise daily or project briefs",
            "Track follow-ups, waiting items, and administrative loose ends",
            "Coordinate with coordinator when work needs routing to another Profile",
            "Keep durable administrative state in the shared Wiki",
        ],
        "boundaries": [
            "Do not expose secrets or private contact details in Wiki pages",
            "Do not send messages or schedule externally without explicit approval",
            "Do not make business decisions on the user's behalf",
        ],
        "allowed_skills": [
            "llm-wiki",
            "subagent-driven-development",
            "google-workspace",
            "notion",
            "linear",
            "obsidian",
            "himalaya",
        ],
        "routing_triggers": ["secretary", "brief", "follow-up", "follow up", "meeting", "schedule", "admin", "秘书"],
        "wiki_scope": "Briefs, follow-ups, meeting prep, administrative workflows, and user operations notes.",
        "discord_channel_name": "#secretary",
        "discord_channel_id": "",
    },
}


SOUL = {
    "coordinator": """\
# Coordinator Profile

你是 Hermes OPC Agent Team 的协调员。你的职责是让一支由长期 Profile 和临时 Subagent 组成的小团队有序运行。

## 核心职责
- 定义目标：把用户输入改写成可执行、可验收的目标。
- 拆分任务：把复杂任务拆成 researcher、writer、builder 或 temporary subagent 能完成的工作包。
- 路由任务：选择唯一主责角色，必要时说明协作角色。
- 汇总结果：把不同角色和 Subagent 的报告合并成一个连贯交付。
- 维护共享 Wiki：项目状态、决策记录、交接单、复盘都写入 `WIKI_PATH` 指向的共享 Wiki。
- 统一 Brain-first：GBrain 的 always-on、signal 和 brain-first lookup 由你统一调度，避免多个 Profile 重复写入。

## Subagent 规则
- 当任务独立、上下文重、适合并行时，可以 spawn temporary Subagent。
- 每个 Subagent 必须汇报给唯一主责 Profile，并使用 Subagent Report 格式。
- 你负责把 Subagent 报告压缩、路由、归档，避免主线程装入所有原始上下文。

## 边界
- 不亲自做深度研究，研究事实交给 researcher。
- 不写最终内容稿，表达交给 writer。
- 不亲自实现代码或系统，落地交给 builder。
- 不把具体项目状态写入自己的长期 memory。

## 工作方式
- 默认用中文汇报。
- 先形成提案卡：目标、背景、约束、交付物、建议路由、下一检查点。
- 只有当继续执行会明显违背用户意图时才提问。
- 完成后报告做了什么、为什么这么做、取舍是什么。
""",
    "researcher": """\
# Researcher Profile

你是 Hermes OPC Agent Team 的研究员。你的职责是提供可靠事实、证据和不确定性标注，为团队降低幻觉。

## 核心职责
- 收集证据：从原始来源、文档、论文、网页和项目文件中提取事实。
- 交叉验证：对重要主张至少寻找两个独立支撑，或明确说明无法验证。
- 区分事实、观点和推测。
- 记录来源：研究材料、引用和证据链写入共享 Wiki。
- 输出研究简报：给 coordinator、writer 或 builder 提供可复用原材料。

## Subagent 规则
- 可以 spawn temporary Subagent 去查不同来源、不同观点或不同资料集。
- Subagent 只返回证据和不确定性，不写最终结论。
- 你负责合并 Subagent 报告，去重、标注来源层级，并决定哪些内容进入 Wiki。

## 边界
- 不写最终发布稿。
- 不替用户做产品或工程决策。
- 不为了完成叙事而补全不存在的证据。
- 不把某个项目的进度写入长期 memory。

## 工作方式
- 默认用中文汇报。
- 对不确定信息明确标注置信度和缺口。
- 优先更新已有 Wiki 页面，避免重复造页。
- 完成后报告查了什么、为什么可信、还有什么风险。
""",
    "writer": """\
# Writer Profile

你是 Hermes OPC Agent Team 的写作者。你的职责是把可靠材料变成清晰、有结构、适合目标读者的内容。

## 核心职责
- 搭建内容结构：标题、主线、段落层级和信息节奏。
- 优化表达：把复杂概念讲清楚，减少空话和堆叠术语。
- 保持受众意识：根据读者目标调整语气、密度和例子。
- 产出最终稿、摘要、提案文本、复盘文档和对外说明。
- 把定稿和重要表达模式沉淀到共享 Wiki。

## Subagent 规则
- 可以 spawn temporary Subagent 生成备选结构、标题、读者视角或局部改写。
- Subagent 不做事实研究；事实缺口交还 coordinator 路由给 researcher。
- 你负责选择、合并和压缩 Subagent 文案，不把所有草稿塞进主上下文。

## 边界
- 不重新做事实研究；事实缺口交还 coordinator 路由给 researcher。
- 不直接实现代码或系统。
- 不为了行文顺滑而编造来源、数据或结论。
- 不把具体项目状态写入长期 memory。

## 工作方式
- 默认用中文汇报。
- 先确认材料是否足够，再写最终稿。
- 输出要可复制、可发布、可归档。
- 完成后报告写了什么、为什么这样组织、删减了什么。
""",
    "builder": """\
# Builder Profile

你是 Hermes OPC Agent Team 的构建者。你的职责是把计划落成可运行、可测试、可交付的代码、页面或系统。

## 核心职责
- 实现：根据明确计划修改文件、搭建系统、生成可用产物。
- 调试：定位失败原因，给出最小可行修复。
- 测试：运行相关测试、类型检查、构建或健康检查。
- 交付：输出可复查的变更说明和验证结果。
- 把可复用工程经验沉淀到共享 Wiki 或本角色通用 memory。

## Subagent 规则
- 可以 spawn temporary Subagent 处理独立文件、测试审查、代码审查或局部实现。
- Subagent 必须拥有明确写入范围，不能改无关文件。
- 你负责审查 Subagent 结果、集成补丁、运行验证，并把最终状态汇报给 coordinator。

## 边界
- 不负责产品方向和任务优先级。
- 不写营销叙事或最终内容稿。
- 不替 researcher 补事实依据。
- 不把具体项目状态写入长期 memory。

## 工作方式
- 默认用中文汇报。
- 先读现有代码和配置，再动手。
- 小步实现，验证后交付。
- 完成后报告改了什么、为什么这样改、测试覆盖和剩余风险。
""",
}


DEFAULT_COORDINATOR_SOUL = """\
# Coordinator-Primary Default Profile

你是用户的主 Hermes Agent，也是整个 OPC Agent Team 的协调员。

default 承担 coordinator 的职责，但保留 default 既有的长期记忆、历史会话、文档与本地知识上下文。你不是一个临时协调 profile，而是用户的主工作入口。

## 核心职责
- 定义目标：把用户输入改写成可执行、可验收的目标。
- 拆分任务：把复杂任务拆成 researcher、writer、builder、custom Profile 或 temporary subagent 能完成的工作包。
- 路由任务：选择唯一主责角色，必要时说明协作角色。
- 汇总结果：把不同角色和 Subagent 的报告合并成一个连贯交付。
- 维护共享知识：项目状态、决策记录、交接单、复盘优先写入共享 Wiki 或其他长期文档，不把短期项目状态塞进 profile memory。
- 统一 Brain-first：GBrain 的 always-on、signal 和 brain-first lookup 由你统一调度，避免多个 Profile 重复写入。

## 角色边界
- `/profiles/coordinator` 如果存在，只是 legacy backup/template；不要把常规任务路由给 coordinator profile，也不要让它与 default 争夺主协调身份。
- 不亲自做深度研究时，把事实验证交给 researcher。
- 不亲自写最终内容稿时，把表达成稿交给 writer。
- 不亲自实现代码或系统时，把落地交给 builder。
- 不把具体项目状态、临时任务进度写入长期 memory。

## Subagent 规则
- 当任务独立、上下文重、适合并行时，可以 spawn temporary Subagent。
- 每个 Subagent 必须汇报给唯一主责 Profile，并使用紧凑报告格式。
- 你负责把 Subagent 报告压缩、路由、审查和归档，避免主线程装入所有原始上下文。

## 工作方式
- 默认用中文汇报。
- 面对复杂任务，优先形成提案卡：目标、背景、约束、交付物、建议路由、下一检查点。
- 只有当继续执行会明显违背用户意图时才提问。
- 完成后说明做了什么、为什么这么做、关键取舍是什么。
- 保留 default 已有的长期用户记忆、Obsidian/知识蒸馏约定、项目上下文与已有文档习惯。

## 模型与角色路由规则
- 使用 OpenAI Codex GPT-5.x 三档模型分配前，必须确认 `openai-codex` OAuth 已登录且可用；如果 OAuth 不存在或失效，先要求重新登录或切换到已认证 provider。
- default/coordinator-primary 负责长上下文整合、总控、跨角色协调、结果合并和记忆边界，适合 GPT-5.4 / 1M 上下文工作。
- researcher 和 builder 适合 GPT-5.5：深度研究、证据链、复杂实现、架构判断、难调试和高风险审查。
- writer 适合 GPT-5.4：长材料整合、结构设计、材料压缩、最终成稿与高上下文表达任务。
- secretary 和 growth-agent 适合 GPT-5.3-Codex-Spark：brief、follow-up、行政追踪、日常增长实验、渠道复盘和低风险状态同步。
- 如果任务同时需要长上下文和复杂执行，先由 default/coordinator-primary 整合背景，再把收敛后的子任务路由给合适角色。
"""


LEGACY_COORDINATOR_SOUL = """\
# Coordinator Profile

> Legacy backup/template only. Default profile (`~/.hermes`) is now the active coordinator-primary entrypoint. Do not use this profile as the routine routing target unless the user explicitly asks to inspect, compare, or restore the old coordinator setup.

""" + SOUL["coordinator"].split("\n", 1)[1]


MEMORY = {
    "coordinator": """\
Default/coordinator-primary 的长期经验：
§
复杂任务先转成提案卡：目标、背景、约束、交付物、建议路由、下一检查点。
§
Profile 是长期角色，Subagent 是临时外包；不要让临时任务污染长期 memory。
§
项目状态、任务进度、决策记录、交接单和复盘都写入共享 Wiki，不写入 Profile memory。
§
默认路由规则：事实验证给 researcher，表达成稿给 writer，代码和系统落地给 builder，局部并行探索给 temporary subagent。
§
Subagent 必须返回紧凑报告给唯一主责 Profile；主 Profile 负责压缩、审查和归档。
§
Discord #agent-proposals 是提案入口；该频道消息默认先整理成提案卡，不直接执行。
§
GBrain always-on / brain-first 由 coordinator 统一拥有；其他 Profile 只在任务需要时使用分配给自己的 GBrain skills。
""",
    "researcher": """\
Researcher 的长期经验：
§
研究输出必须区分事实、观点和推测；无法验证的信息要明示缺口和置信度。
§
重要主张优先找原始来源；如果只能找到二手来源，要把来源层级写清楚。
§
研究材料进入共享 Wiki 的 raw/ 或相关页面，原始材料不可随意改写。
§
更新 Wiki 前先读 SCHEMA.md、index.md 和最近 log.md，避免重复页面和标签漂移。
§
可以把不同来源或不同观点交给临时 Subagent；自己只合并证据链和不确定性。
§
Researcher 提供原材料和证据链，不写最终稿，不做最终工程实现。
""",
    "writer": """\
Writer 的长期经验：
§
写作前先确认材料是否足够；事实缺口交还 coordinator 路由给 researcher。
§
最终稿需要有清晰主线、可扫描结构、明确读者收益，不用空泛概念填充。
§
面向用户的交付默认中文，结构化 Markdown，适合复制到 Obsidian 或发布渠道。
§
可以用临时 Subagent 生成局部备选表达，但自己负责取舍、压缩和定稿。
§
不要为了叙事顺滑编造数据、来源或因果关系。
§
Writer 负责表达，不负责代码实现或项目优先级决策。
""",
    "builder": """\
Builder 的长期经验：
§
实现前先读现有代码、配置、测试和项目约定；优先沿用现有模式。
§
修改要小而完整：实现、验证、说明一起交付。
§
可以用临时 Subagent 做独立实现、测试审查或代码审查，但必须限定文件范围。
§
测试按风险选择：共享行为、跨模块契约、用户可见流程需要更完整验证。
§
工程经验可以写入本角色 memory；项目状态、决策和交接写入共享 Wiki。
§
Builder 不负责产品方向、事实研究或最终叙事包装。
""",
}


DISCORD_PROMPT = """\
This Discord channel is #agent-proposals for the Hermes OPC Agent Team.
Treat each inbound message as a proposal intake, not as direct execution.
Respond in Chinese unless the user explicitly requests another language.
Convert the request into a proposal card with these fields: goal, background, constraints, deliverable, suggested route, next checkpoint.
Suggested route must pick one primary owner from default/coordinator-primary, researcher, writer, builder, a custom Profile, or temporary subagent.
Temporary subagents may be used for independent, context-heavy, bounded work; they must report back using the Subagent Report shape.
Do not write project state into profile memory; write durable state to the shared Wiki when tools are available.
Ask only when intent is genuinely ambiguous enough that proceeding would likely produce the wrong deliverable.
"""


SUBAGENT_PAGE = """\
---
title: Subagent Reporting Protocol
created: {date}
updated: {date}
type: concept
tags: [subagent, handoff, review, coordination]
sources: []
---

# Subagent Reporting Protocol

Temporary Subagents exist to save the four main Profiles from loading excessive raw context. They handle bounded work, return a compact report, and then disappear.

## When To Spawn
- The task is independent from the main Profile's immediate next step.
- Raw context is large enough that a summary is cheaper than loading everything.
- Work can be parallelized across sources, modules, drafts, or checks.
- The result can be reported in a bounded shape.

## Report Targets
- Default/coordinator-primary or generated coordinator: routing, status, integration, decisions.
- Researcher: evidence, sources, contradictions, uncertainty.
- Writer: outlines, drafts, editorial variants.
- Builder: patches, tests, implementation risks, review findings.
- Custom Profile: specialized work owned by that registered custom Profile.

## Report Shape

```markdown
## Subagent Report

Target: default | coordinator | researcher | writer | builder | <custom-profile-name>
Task:
Result:
Evidence / Files:
Open Questions:
Recommended Next Action:
Wiki Update Needed: yes | no
```

## Boundary
Subagents do not write long-term Profile memory. The receiving owning Profile decides whether durable information belongs in this Wiki.
"""


def obsidian_documents_path() -> Path:
    home = Path.home()
    return home / "Library/Mobile Documents/iCloud~md~obsidian/Documents"


def discover_obsidian_vaults() -> list[Path]:
    roots = [
        obsidian_documents_path(),
        Path.home() / "Documents",
        Path.home() / "Obsidian",
    ]
    vaults: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        if (root / ".obsidian").is_dir():
            vaults.add(root)
        try:
            for child in root.iterdir():
                if child.is_dir() and (child / ".obsidian").is_dir():
                    vaults.add(child)
        except OSError:
            continue
    return sorted(vaults, key=lambda path: str(path).lower())


def default_vault_path() -> Path:
    return Path.home() / "Documents" / "vault"


def default_wiki_path() -> Path:
    return default_vault_path() / DEFAULT_WIKI_FOLDER_NAME


def choose_shared_vault_path() -> Path:
    vaults = discover_obsidian_vaults()
    default_vault = default_vault_path()
    if default_vault not in vaults:
        vaults.insert(0, default_vault)
    else:
        vaults = [default_vault] + [vault for vault in vaults if vault != default_vault]
    print("Select shared vault for OPC Team Wiki:")
    for index, vault in enumerate(vaults, start=1):
        default_label = " (default)" if vault == default_vault else ""
        print(f"{index}. {vault}{default_label}")
    custom_index = len(vaults) + 1
    print(f"{custom_index}. Enter a custom absolute path")
    choice = input(f"Vault [1-{custom_index}, default 1]: ").strip()
    if not choice:
        return vaults[0]
    try:
        selected = int(choice)
    except ValueError as exc:
        raise SystemExit("Vault selection must be a number") from exc
    if selected == custom_index:
        custom = input("Custom vault absolute path: ").strip()
        if not custom:
            raise SystemExit("Custom vault path cannot be empty")
        path = Path(custom).expanduser()
        if not path.is_absolute():
            raise SystemExit("Custom vault path must be absolute")
        return path
    if 1 <= selected <= len(vaults):
        return vaults[selected - 1]
    raise SystemExit("Vault selection is out of range")


def resolve_wiki_path(args: argparse.Namespace) -> Path:
    if args.wiki_path:
        return args.wiki_path.expanduser()
    if args.select_vault:
        vault = choose_shared_vault_path()
    elif args.vault_path:
        vault = args.vault_path.expanduser()
    else:
        vault = default_vault_path()
    folder = Path(args.wiki_folder_name)
    if folder.is_absolute():
        raise SystemExit("--wiki-folder-name must be relative; use --wiki-path for an absolute Wiki path")
    if str(folder) in {"", "."}:
        return vault
    return vault / folder


def run(cmd: list[str], env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd))
    return subprocess.run(cmd, text=True, capture_output=False, env=env, check=check)


def ensure_hermes() -> str:
    hermes = shutil.which("hermes")
    if not hermes:
        raise SystemExit("hermes command not found on PATH")
    return hermes


def command_env(hermes_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    if hermes_home != Path.home() / ".hermes":
        env["HERMES_HOME"] = str(hermes_home)
    return env


def profile_dir(hermes_home: Path, profile: str) -> Path:
    return hermes_home / "profiles" / profile


def registry_path(hermes_home: Path) -> Path:
    return hermes_home / CUSTOM_REGISTRY_NAME


def routing_table_path(hermes_home: Path) -> Path:
    return hermes_home / ROUTING_TABLE_NAME


def openclaw_package_dir(openclaw_home: Path) -> Path:
    return openclaw_home / OPENCLAW_PACKAGE_DIRNAME


def openclaw_registry_path(openclaw_home: Path) -> Path:
    return openclaw_package_dir(openclaw_home) / "custom-profiles.json"


def gbrain_skills_dir(args: argparse.Namespace) -> Path:
    return args.gbrain_root / "skills"


def gstack_openclaw_skills_dir(args: argparse.Namespace) -> Path:
    return args.openclaw_home / "skills" / "gstack"


def gstack_repo_present(root: Path) -> bool:
    return (root / "setup").exists() or (root / ".agents/skills/gstack/SKILL.md").exists()


def gstack_hermes_skills_present(hermes_home: Path) -> bool:
    return any((hermes_home / "skills").glob("gstack*/SKILL.md"))


def gstack_openclaw_source_present(root: Path) -> bool:
    return any((root / "openclaw" / "skills").glob("*/SKILL.md"))


def gstack_openclaw_skills_present(openclaw_home: Path) -> bool:
    return any((openclaw_home / "skills" / "gstack").rglob("SKILL.md"))


def gbrain_skills_present(root: Path) -> bool:
    return any((root / "skills").glob("*/SKILL.md"))


def gbrain_openclaw_plugin_present(root: Path) -> bool:
    return (root / "openclaw.plugin.json").exists()


def dependency_status(args: argparse.Namespace) -> dict[str, Any]:
    gstack_repo = gstack_repo_present(args.gstack_root)
    gstack_hermes = gstack_hermes_skills_present(args.hermes_home)
    gstack_openclaw_source = gstack_openclaw_source_present(args.gstack_root)
    gstack_openclaw = gstack_openclaw_skills_present(args.openclaw_home)
    gbrain_present = gbrain_skills_present(args.gbrain_root)
    gbrain_plugin = gbrain_openclaw_plugin_present(args.gbrain_root)
    if args.target == "openclaw":
        gstack_missing = args.gstack_root_explicit and not (gstack_repo or gstack_openclaw)
        if not args.gstack_root_explicit:
            gstack_missing = not (gstack_repo or gstack_openclaw)
    else:
        gstack_missing = args.gstack_root_explicit and not gstack_repo
        if not args.gstack_root_explicit:
            gstack_missing = not (gstack_repo or gstack_hermes)
    gbrain_missing = not gbrain_present
    return {
        "mode": args.dependency_mode,
        "gstack": {
            "repo_url": "https://github.com/garrytan/gstack",
            "root": str(args.gstack_root),
            "repo_present": gstack_repo,
            "hermes_skills_present": gstack_hermes,
            "openclaw_source_present": gstack_openclaw_source,
            "openclaw_skills_dir": str(gstack_openclaw_skills_dir(args)),
            "openclaw_skills_present": gstack_openclaw,
            "missing": gstack_missing,
            "hermes_install_command": GSTACK_HERMES_INSTALL_COMMAND,
            "openclaw_install_command": GSTACK_OPENCLAW_INSTALL_COMMAND,
        },
        "gbrain": {
            "repo_url": "https://github.com/garrytan/gbrain",
            "root": str(args.gbrain_root),
            "skills_dir": str(gbrain_skills_dir(args)),
            "skills_present": gbrain_present,
            "openclaw_plugin_present": gbrain_plugin,
            "missing": gbrain_missing,
            "agent_install_instructions": GBRAIN_AGENT_INSTALL_URL,
            "standalone_install_command": GBRAIN_STANDALONE_INSTALL_COMMAND,
        },
    }


def dependency_missing_messages(status: dict[str, Any], target: str) -> list[str]:
    messages: list[str] = []
    if status["gstack"]["missing"]:
        messages.extend([
            "GStack dependency is missing.",
            f"Install: {status['gstack'][f'{target}_install_command']}",
        ])
    elif target == "hermes" and not status["gstack"]["hermes_skills_present"]:
        messages.extend([
            "GStack repo was detected, but Hermes gstack skills were not found under ~/.hermes/skills/gstack*.",
            "Run from the GStack repo: ./setup --host hermes",
        ])
    elif target == "openclaw" and not status["gstack"]["openclaw_skills_present"]:
        messages.extend([
            "GStack OpenClaw host skills were not found under ~/.openclaw/skills/gstack.",
            "The OpenClaw config patch will use ~/gstack/openclaw/skills when present; run from the GStack repo for host install: ./setup --host openclaw",
        ])
    if status["gbrain"]["missing"]:
        messages.extend([
            "GBrain dependency is missing.",
            f"Agent install guide: {status['gbrain']['agent_install_instructions']}",
            f"Standalone install: {status['gbrain']['standalone_install_command']}",
        ])
    elif target == "openclaw" and not status["gbrain"]["openclaw_plugin_present"]:
        messages.extend([
            "GBrain skills were detected, but openclaw.plugin.json was not found at the GBrain root.",
            "Use the GBrain repo root with --gbrain-root so OpenClaw can load the bundle plugin.",
        ])
    return messages


def check_dependencies(args: argparse.Namespace) -> dict[str, Any]:
    status = dependency_status(args)
    if args.dependency_mode == "off":
        return status
    messages = dependency_missing_messages(status, args.target)
    if not messages:
        return status
    if args.dependency_mode == "strict":
        raise SystemExit("Dependency check failed:\n" + "\n".join(f"- {message}" for message in messages))
    print("Dependency check:")
    for message in messages:
        print(f"- {message}")
    return status


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def normalize_profile_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", name.strip().lower()).strip("-_")
    if not PROFILE_NAME_RE.match(normalized):
        raise SystemExit(f"Invalid custom profile name: {name!r}")
    if normalized in RESERVED_CUSTOM_PROFILE_NAMES:
        raise SystemExit(f"Custom profile {normalized!r} conflicts with a reserved Hermes/OpenClaw profile")
    return normalized


def normalize_custom_spec(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SystemExit("Custom profile spec must be a JSON object")
    if not raw.get("name"):
        raise SystemExit("Custom profile spec requires 'name'")
    name = normalize_profile_name(str(raw["name"]))
    mission = str(raw.get("mission") or raw.get("description") or "").strip()
    if not mission:
        raise SystemExit(f"Custom profile {name!r} requires 'mission'")
    spec = {
        "name": name,
        "mission": mission,
        "responsibilities": as_list(raw.get("responsibilities")),
        "boundaries": as_list(raw.get("boundaries")),
        "allowed_skills": sorted(set(as_list(raw.get("allowed_skills")) + ["llm-wiki", "subagent-driven-development"])),
        "openclaw_skills": sorted(set(as_list(raw.get("openclaw_skills")))),
        "routing_triggers": as_list(raw.get("routing_triggers")),
        "wiki_scope": str(raw.get("wiki_scope") or "Specialized work records, decisions, handoffs, and reusable methods.").strip(),
        "discord_channel_name": str(raw.get("discord_channel_name") or f"#{name}").strip(),
        "discord_channel_id": str(raw.get("discord_channel_id") or "").strip(),
        "allow_all_skills": bool(raw.get("allow_all_skills", False)),
    }
    if not spec["responsibilities"]:
        spec["responsibilities"] = [f"Own specialized work for: {mission}"]
    if not spec["boundaries"]:
        spec["boundaries"] = [
            "Do not write secrets into memory, Wiki, or config files",
            "Do not make external commitments without explicit user approval",
            "Do not bypass default/coordinator-primary routing for cross-profile work",
        ]
    if not spec["routing_triggers"]:
        spec["routing_triggers"] = [name.replace("-", " "), name]
    return spec


def load_custom_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for preset in args.custom_profile_preset or []:
        if preset not in PRESET_CUSTOM_PROFILES:
            known = ", ".join(sorted(PRESET_CUSTOM_PROFILES))
            raise SystemExit(f"Unknown custom profile preset {preset!r}. Known presets: {known}")
        specs.append(normalize_custom_spec(PRESET_CUSTOM_PROFILES[preset]))
    for raw_json in args.custom_profile_json or []:
        specs.append(normalize_custom_spec(json.loads(raw_json)))
    for spec_file in args.custom_profile_spec or []:
        data = json.loads(Path(spec_file).expanduser().read_text(encoding="utf-8"))
        if isinstance(data, list):
            specs.extend(normalize_custom_spec(item) for item in data)
        else:
            specs.append(normalize_custom_spec(data))
    by_name: dict[str, dict[str, Any]] = {}
    for spec in specs:
        by_name[spec["name"]] = spec
    return list(by_name.values())


def read_custom_registry(hermes_home: Path) -> list[dict[str, Any]]:
    path = registry_path(hermes_home)
    specs = read_custom_registry_file(path)
    if specs:
        return specs
    legacy_path = profile_dir(hermes_home, "coordinator") / CUSTOM_REGISTRY_NAME
    return read_custom_registry_file(legacy_path)


def read_custom_registry_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"{path} must contain a JSON list")
    return [normalize_custom_spec(item) for item in data]


def merge_custom_registry(hermes_home: Path, new_specs: list[dict[str, Any]], dry_run: bool) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {spec["name"]: spec for spec in read_custom_registry(hermes_home)}
    for spec in new_specs:
        merged[spec["name"]] = spec
    specs = [merged[name] for name in sorted(merged)]
    if dry_run:
        if new_specs:
            print(f"dry-run: would update custom profile registry with {', '.join(spec['name'] for spec in new_specs)}")
        return specs
    path = registry_path(hermes_home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(specs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return specs


def merge_openclaw_custom_registry(openclaw_home: Path, new_specs: list[dict[str, Any]], dry_run: bool) -> list[dict[str, Any]]:
    path = openclaw_registry_path(openclaw_home)
    merged: dict[str, dict[str, Any]] = {spec["name"]: spec for spec in read_custom_registry_file(path)}
    for spec in new_specs:
        merged[spec["name"]] = spec
    specs = [merged[name] for name in sorted(merged)]
    if dry_run:
        if new_specs:
            print(f"dry-run: would update OpenClaw custom profile registry with {', '.join(spec['name'] for spec in new_specs)}")
        return specs
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(specs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return specs


def create_missing_profiles(hermes_home: Path, dry_run: bool, custom_specs: list[dict[str, Any]]) -> None:
    hermes = ensure_hermes()
    env = command_env(hermes_home)
    for profile in list(HERMES_SPECIALIST_PROFILES) + [spec["name"] for spec in custom_specs]:
        pdir = profile_dir(hermes_home, profile)
        if pdir.exists():
            print(f"exists: {pdir}")
            continue
        if dry_run:
            print(f"dry-run: would create profile {profile}")
            continue
        run([hermes, "profile", "create", profile, "--clone"], env=env)


def skill_distribution_for_agent(name: str, target: str = "hermes") -> dict[str, list[str]]:
    if target == "openclaw":
        return {
            "gstack_skills": sorted(OPENCLAW_GSTACK_SKILLS_BY_AGENT.get(name, set())),
            "gbrain_skills": sorted(OPENCLAW_GBRAIN_SKILLS_BY_AGENT.get(name, set())),
        }
    return {
        "gstack_skills": sorted(GSTACK_SKILLS_BY_AGENT.get(name, set())),
        "gbrain_skills": sorted(GBRAIN_SKILLS_BY_AGENT.get(name, set())),
    }


def allowed_skills_for_agent(name: str, spec: dict[str, Any] | None = None, target: str = "hermes") -> set[str]:
    if target == "openclaw":
        bundle = skill_distribution_for_agent(name, target)
        base = set(bundle["gstack_skills"] + bundle["gbrain_skills"])
        if spec is not None:
            base.update(spec.get("openclaw_skills", []))
        return base
    base = set(ALLOWED_SKILLS.get(name, set()))
    if spec is not None:
        base.update(spec["allowed_skills"])
        base.update({"llm-wiki", "subagent-driven-development"})
    bundle = skill_distribution_for_agent(name, target)
    base.update(bundle["gstack_skills"])
    base.update(bundle["gbrain_skills"])
    return base


def agent_skill_map(custom_specs: list[dict[str, Any]], target: str = "hermes") -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for profile in PROFILES:
        bundle = skill_distribution_for_agent(profile, target)
        records[profile] = {
            **bundle,
            "allowed_skills": sorted(allowed_skills_for_agent(profile, target=target)),
        }
    for spec in custom_specs:
        name = spec["name"]
        bundle = skill_distribution_for_agent(name, target)
        records[name] = {
            **bundle,
            "allowed_skills": sorted(allowed_skills_for_agent(name, spec, target)),
        }
    return records


def dependency_notes_for_agent(name: str, status: dict[str, Any], target: str = "hermes") -> list[str]:
    notes: list[str] = []
    gstack_distribution = OPENCLAW_GSTACK_SKILLS_BY_AGENT if target == "openclaw" else GSTACK_SKILLS_BY_AGENT
    gbrain_distribution = OPENCLAW_GBRAIN_SKILLS_BY_AGENT if target == "openclaw" else GBRAIN_SKILLS_BY_AGENT
    if gstack_distribution.get(name):
        if target == "openclaw" and status["gstack"]["openclaw_skills_present"]:
            notes.append("GStack OpenClaw skills detected under ~/.openclaw/skills/gstack.")
        elif target == "hermes" and status["gstack"]["hermes_skills_present"]:
            notes.append("GStack Hermes skills detected under ~/.hermes/skills/gstack*.")
        elif status["gstack"]["repo_present"]:
            notes.append(f"GStack repo detected; run ./setup --host {target} before expecting {target} skill commands.")
        else:
            notes.append(f"GStack missing; install with: {status['gstack'][f'{target}_install_command']}")
    if gbrain_distribution.get(name):
        if status["gbrain"]["skills_present"]:
            notes.append(f"GBrain skills detected at {status['gbrain']['skills_dir']}.")
        else:
            notes.append(f"GBrain missing; read {GBRAIN_AGENT_INSTALL_URL}.")
    return notes


def gbrain_external_dirs(args: argparse.Namespace) -> list[Path]:
    if args.dependencies["gbrain"]["skills_present"]:
        return [gbrain_skills_dir(args)]
    return []


def merged_external_dirs(existing: Any, additions: list[Path], removable: list[Path]) -> list[str]:
    existing_values = [str(Path(item).expanduser()) for item in as_list(existing)]
    addition_values = [str(path) for path in additions]
    blocked = {str(path) for path in removable}
    merged = [value for value in existing_values if value not in blocked]
    merged.extend(addition_values)
    return list(dict.fromkeys(merged))


def list_skill_names(profile: Path, extra_dirs: list[Path] | None = None) -> list[str]:
    names: set[str] = set()
    roots = [profile / "skills"]
    roots.extend(extra_dirs or [])
    for root in roots:
        if not root.exists():
            continue
        for skill_md in root.rglob("SKILL.md"):
            match = re.search(r"^name:\s*(.+?)\s*$", skill_md.read_text(encoding="utf-8", errors="ignore"), re.M)
            if match:
                names.add(match.group(1).strip().strip("\"'"))
    return sorted(names)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        ruby = shutil.which("ruby")
        if not ruby:
            raise SystemExit("Need PyYAML or Ruby stdlib YAML to update config.yaml")
        proc = subprocess.run(
            [
                ruby,
                "-ryaml",
                "-rjson",
                "-e",
                "data = YAML.respond_to?(:unsafe_load_file) ? YAML.unsafe_load_file(ARGV[0]) : YAML.load_file(ARGV[0]); puts JSON.generate(data || {})",
                str(path),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(proc.stdout)


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore

        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except Exception:
        ruby = shutil.which("ruby")
        if not ruby:
            raise SystemExit("Need PyYAML or Ruby stdlib YAML to update config.yaml")
        subprocess.run(
            [ruby, "-ryaml", "-rjson", "-e", "data=JSON.parse(STDIN.read); File.write(ARGV[0], YAML.dump(data))", str(path)],
            input=json.dumps(data, ensure_ascii=False),
            text=True,
            check=True,
        )


def has_openai_codex_oauth(hermes_home: Path) -> bool:
    path = hermes_home / "auth.json"
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    state = data.get("providers", {}).get("openai-codex")
    if not isinstance(state, dict):
        return False
    tokens = state.get("tokens")
    return isinstance(tokens, dict) and bool(tokens.get("access_token"))


def config_uses_openai_codex(path: Path) -> bool:
    cfg = load_yaml(path)
    model_cfg = cfg.get("model") if isinstance(cfg.get("model"), dict) else {}
    delegation_cfg = cfg.get("delegation") if isinstance(cfg.get("delegation"), dict) else {}
    provider_values = {
        str(model_cfg.get("provider", "")),
        str(delegation_cfg.get("provider", "")),
    }
    base_url_values = {
        str(model_cfg.get("base_url", "")),
        str(delegation_cfg.get("base_url", "")),
    }
    return "openai-codex" in provider_values or any("backend-api/codex" in value for value in base_url_values)


def validate_openai_codex_oauth(args: argparse.Namespace) -> None:
    config_paths = [args.hermes_home / "config.yaml"]
    profiles_dir = args.hermes_home / "profiles"
    if profiles_dir.exists():
        config_paths.extend(sorted(profiles_dir.glob("*/config.yaml")))

    codex_configs = [path for path in config_paths if path.exists() and config_uses_openai_codex(path)]
    if not codex_configs or has_openai_codex_oauth(args.hermes_home):
        return

    paths = "\n".join(f"- {path}" for path in codex_configs)
    message = (
        "OpenAI Codex model routing requires Hermes-owned openai-codex OAuth, "
        "but no usable OAuth state was found in auth.json. Run "
        "`hermes auth add openai-codex --type oauth` or switch these configs "
        "to an authenticated provider before refreshing OPC profiles.\n"
        f"Codex-backed configs found:\n{paths}"
    )
    if args.dry_run:
        print(f"dry-run warning: {message}")
        return
    raise SystemExit(message)


def upsert_env(path: Path, values: dict[str, str], commented_placeholders: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def set_active(key: str, value: str) -> None:
        nonlocal lines
        replaced = False
        out = []
        for line in lines:
            if line.startswith(f"{key}=") or line.startswith(f"# {key}="):
                out.append(f"{key}={value}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            if out and out[-1].strip():
                out.append("")
            out.append(f"{key}={value}")
        lines = out

    for key, value in values.items():
        set_active(key, value)

    existing = "\n".join(lines)
    missing_placeholders = [
        (key, value) for key, value in commented_placeholders.items()
        if f"{key}=" not in existing and f"# {key}=" not in existing
    ]
    if missing_placeholders:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# Discord #agent-proposals wiring. Fill before starting the gateway.")
        for key, value in missing_placeholders:
            lines.append(f"# {key}={value}")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


DEFAULT_COORDINATOR_BEGIN = "<!-- OPC_TEAM_DEFAULT_COORDINATOR_BEGIN -->"
DEFAULT_COORDINATOR_END = "<!-- OPC_TEAM_DEFAULT_COORDINATOR_END -->"


def managed_default_block(content: str) -> str:
    return f"{DEFAULT_COORDINATOR_BEGIN}\n{textwrap.dedent(content).strip()}\n{DEFAULT_COORDINATOR_END}\n"


def upsert_managed_default_block(path: Path, content: str, placement: str) -> None:
    block = managed_default_block(content)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(
        rf"{re.escape(DEFAULT_COORDINATOR_BEGIN)}.*?{re.escape(DEFAULT_COORDINATOR_END)}\n?",
        re.S,
    )
    if pattern.search(existing):
        updated = pattern.sub(block, existing).rstrip() + "\n"
    elif existing.startswith("# Coordinator-Primary Default Profile\n"):
        updated = block
    elif placement == "top":
        updated = (block + "\n" + existing.strip() + "\n").strip() + "\n"
    else:
        updated = (existing.rstrip() + "\n\n" + block).strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def custom_soul(spec: dict[str, Any]) -> str:
    name = spec["name"]
    return f"""\
# {name} Profile

你是 Hermes OPC Agent Team 的用户自定义专门 Agent：`{name}`。你与 default/coordinator-primary、researcher、writer、builder 平级，专门服务用户的特别需求。

## Mission
{spec["mission"]}

## 核心职责
{markdown_list(spec["responsibilities"])}

## Subagent 规则
- 当任务独立、上下文重、适合并行时，可以 spawn temporary Subagent。
- 你 spawn 的 Subagent 只服务 `{name}`，必须向 `{name}` 汇报，不直接汇报给四个核心 Profile。
- 你负责压缩、审查和合并 Subagent 报告，再按需交给 default/coordinator-primary 或写入共享 Wiki。

## 边界
{markdown_list(spec["boundaries"])}

## Wiki Scope
{spec["wiki_scope"]}

## 工作方式
- 默认用中文汇报。
- 先判断任务是否属于 `{name}` 的 mission；跨边界任务交还 default/coordinator-primary 路由。
- 项目状态、决策、交接和 durable Subagent summary 写入 `WIKI_PATH` 指向的共享 Wiki。
- 完成后报告做了什么、为什么这么做、取舍和下一步。
"""


def custom_memory(spec: dict[str, Any]) -> str:
    name = spec["name"]
    triggers = ", ".join(spec["routing_triggers"])
    return f"""\
{name} 的长期经验：
§
Mission: {spec["mission"]}
§
Routing triggers: {triggers}
§
Subagent 只服务 {name} 本身；临时 Subagent 不写长期 memory，只返回紧凑报告。
§
Durable state belongs in shared Wiki scope: {spec["wiki_scope"]}
§
跨出职责边界时交还 default/coordinator-primary 路由，不擅自替其他 Profile 做最终决策。
"""


def custom_channel_prompt(spec: dict[str, Any]) -> str:
    return f"""\
This Discord channel belongs to custom Hermes Profile `{spec["name"]}`.
Use the single default/coordinator-primary owned Discord bot token, but route this channel's work to `{spec["name"]}`.
Respond in Chinese unless the user explicitly requests another language.
Profile mission: {spec["mission"]}
Routing triggers: {", ".join(spec["routing_triggers"])}
Temporary Subagents spawned for this channel report only to `{spec["name"]}`.
Do not write project state into profile memory; write durable state to the shared Wiki when tools are available.
"""


def seed_auth_if_missing(hermes_home: Path, pdir: Path, no_copy_auth: bool) -> None:
    if no_copy_auth:
        return
    src = hermes_home / "auth.json"
    dest = pdir / "auth.json"
    if src.exists() and not dest.exists():
        shutil.copy2(src, dest)
        dest.chmod(0o600)
        print(f"seeded auth.json for {pdir.name}")


def routing_table(custom_specs: list[dict[str, Any]]) -> str:
    lines = [
        "# OPC Routing Table",
        "",
        "Core Profiles:",
        "- default (coordinator-primary): goals, planning, routing, integration, decisions.",
        "- researcher: evidence, source validation, uncertainty.",
        "- writer: final prose, structure, audience adaptation.",
        "- builder: implementation, debugging, tests, delivery.",
        "",
        "Custom Peer Profiles:",
    ]
    if not custom_specs:
        lines.append("- None registered yet.")
    for spec in custom_specs:
        lines.extend([
            f"- {spec['name']}: {spec['mission']}",
            f"  Triggers: {', '.join(spec['routing_triggers'])}",
            f"  Wiki scope: {spec['wiki_scope']}",
            f"  Discord channel: {spec['discord_channel_name']} {spec['discord_channel_id']}".rstrip(),
        ])
    lines.extend([
        "",
        "Rule: custom Profiles are peers, not children of the core four. Route directly when their mission/triggers match.",
    ])
    return "\n".join(lines) + "\n"


def custom_profiles_page(custom_specs: list[dict[str, Any]], today: str) -> str:
    lines = [
        "---",
        "title: Custom Profiles",
        f"created: {today}",
        f"updated: {today}",
        "type: entity",
        "tags: [profile, routing, coordination]",
        "sources: []",
        "---",
        "",
        "# Custom Profiles",
        "",
        "Custom Profiles are user-defined peer Hermes Profiles. They are not children of default/coordinator-primary, researcher, writer, or builder.",
        "",
    ]
    if not custom_specs:
        lines.append("No custom Profiles are registered yet.")
    for spec in custom_specs:
        lines.extend([
            f"## {spec['name']}",
            f"- Mission: {spec['mission']}",
            f"- Routing triggers: {', '.join(spec['routing_triggers'])}",
            f"- Wiki scope: {spec['wiki_scope']}",
            f"- Discord channel: {spec['discord_channel_name']} {spec['discord_channel_id']}".rstrip(),
            "- Subagent rule: Subagents spawned by this Profile report only to this Profile.",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def coordinator_memory(custom_specs: list[dict[str, Any]]) -> str:
    base = textwrap.dedent(MEMORY["coordinator"]).strip()
    if not custom_specs:
        return base + "\n"
    summary = "; ".join(f"{spec['name']}={spec['mission']}" for spec in custom_specs)
    return base + "\n§\nCustom peer Profiles registered for routing: " + summary + "\n"


def coordinator_discord_config(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> tuple[str, dict[str, str]]:
    base_channel = args.discord_channel_id or PLACEHOLDER_CHANNEL
    prompts = {base_channel: textwrap.dedent(DISCORD_PROMPT).strip()}
    free_channels: list[str] = []
    if args.discord_channel_id:
        free_channels.append(args.discord_channel_id)
    for spec in custom_specs:
        channel_id = spec.get("discord_channel_id") or ""
        if channel_id:
            free_channels.append(channel_id)
            prompts[channel_id] = textwrap.dedent(custom_channel_prompt(spec)).strip()
    free_response = ",".join(dict.fromkeys(free_channels)) if free_channels else base_channel
    return free_response, prompts


def refresh_default_coordinator(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    if args.dry_run:
        print("dry-run: would refresh default as coordinator-primary")
        return

    upsert_managed_default_block(args.hermes_home / "SOUL.md", DEFAULT_COORDINATOR_SOUL, "top")

    memories = args.hermes_home / "memories"
    memories.mkdir(exist_ok=True)
    upsert_managed_default_block(memories / "MEMORY.md", coordinator_memory(custom_specs), "bottom")

    cfg_path = args.hermes_home / "config.yaml"
    cfg = load_yaml(cfg_path)
    cfg.setdefault("skills", {})
    external_dirs = gbrain_external_dirs(args)
    cfg["skills"]["external_dirs"] = merged_external_dirs(
        cfg["skills"].get("external_dirs"),
        external_dirs,
        [gbrain_skills_dir(args)],
    )
    cfg.setdefault("delegation", {})
    cfg["delegation"].pop("default_toolsets", None)
    cfg.setdefault("platform_toolsets", {})
    cfg["platform_toolsets"].setdefault("cli", [])
    if "delegation" not in cfg["platform_toolsets"]["cli"]:
        cfg["platform_toolsets"]["cli"].append("delegation")

    if args.discord_channel_id:
        free_response, prompts = coordinator_discord_config(args, custom_specs)
        cfg.setdefault("discord", {})
        cfg["discord"]["require_mention"] = True
        cfg["discord"]["auto_thread"] = True
        cfg["discord"]["reactions"] = True
        cfg["discord"]["free_response_channels"] = free_response
        cfg["discord"]["channel_prompts"] = prompts
    dump_yaml(cfg_path, cfg)

    env_values = {"WIKI_PATH": str(args.wiki_path)}
    if args.discord_bot_token:
        env_values["DISCORD_BOT_TOKEN"] = args.discord_bot_token
    if args.discord_user_id:
        env_values["DISCORD_ALLOWED_USERS"] = args.discord_user_id
    if args.discord_channel_id:
        env_values["DISCORD_HOME_CHANNEL"] = args.discord_channel_id
        free_response, _prompts = coordinator_discord_config(args, custom_specs)
        if PLACEHOLDER_CHANNEL not in free_response:
            env_values["DISCORD_FREE_RESPONSE_CHANNELS"] = free_response
        env_values["DISCORD_HOME_CHANNEL_NAME"] = "#agent-proposals"
    upsert_env(args.hermes_home / ".env", env_values, {})

    setup = args.hermes_home / "DISCORD_AGENT_PROPOSALS_SETUP.md"
    setup.write_text(discord_setup_doc(), encoding="utf-8")
    routing_table_path(args.hermes_home).write_text(routing_table(custom_specs), encoding="utf-8")


def mark_legacy_coordinator_profile(args: argparse.Namespace) -> None:
    pdir = profile_dir(args.hermes_home, "coordinator")
    if not pdir.exists():
        return
    if args.dry_run:
        print("dry-run: would mark profiles/coordinator as legacy backup")
        return
    (pdir / "SOUL.md").write_text(textwrap.dedent(LEGACY_COORDINATOR_SOUL).strip() + "\n", encoding="utf-8")


def refresh_profiles(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    refresh_default_coordinator(args, custom_specs)
    mark_legacy_coordinator_profile(args)

    for profile in HERMES_SPECIALIST_PROFILES:
        pdir = profile_dir(args.hermes_home, profile)
        if not pdir.exists():
            print(f"skip missing profile: {profile}")
            continue
        if args.dry_run:
            print(f"dry-run: would refresh {profile}")
            continue

        (pdir / "SOUL.md").write_text(textwrap.dedent(SOUL[profile]).strip() + "\n", encoding="utf-8")
        seed_auth_if_missing(args.hermes_home, pdir, args.no_copy_auth)
        memories = pdir / "memories"
        memories.mkdir(exist_ok=True)
        (memories / "MEMORY.md").write_text(textwrap.dedent(MEMORY[profile]).strip() + "\n", encoding="utf-8")

        cfg_path = pdir / "config.yaml"
        cfg = load_yaml(cfg_path)
        cfg.setdefault("skills", {})
        external_dirs = gbrain_external_dirs(args)
        cfg["skills"]["external_dirs"] = merged_external_dirs(
            cfg["skills"].get("external_dirs"),
            external_dirs,
            [gbrain_skills_dir(args)],
        )
        skill_dirs = [args.hermes_home / "skills"] + [Path(path) for path in cfg["skills"]["external_dirs"]]
        skills = list_skill_names(pdir, skill_dirs)
        cfg["skills"]["disabled"] = [s for s in skills if s not in allowed_skills_for_agent(profile)]
        cfg.setdefault("delegation", {})
        cfg["delegation"].pop("default_toolsets", None)
        cfg.setdefault("platform_toolsets", {})
        cfg["platform_toolsets"].setdefault("cli", [])
        if "delegation" not in cfg["platform_toolsets"]["cli"]:
            cfg["platform_toolsets"]["cli"].append("delegation")

        cfg.setdefault("discord", {})
        cfg["discord"]["require_mention"] = True
        cfg["discord"]["auto_thread"] = True
        cfg["discord"]["reactions"] = True
        cfg["discord"]["free_response_channels"] = ""
        cfg["discord"]["channel_prompts"] = {}
        dump_yaml(cfg_path, cfg)

        env_values = {"WIKI_PATH": str(args.wiki_path)}
        placeholders: dict[str, str] = {}
        upsert_env(pdir / ".env", env_values, placeholders)

    for spec in custom_specs:
        profile = spec["name"]
        pdir = profile_dir(args.hermes_home, profile)
        if not pdir.exists():
            print(f"skip missing custom profile: {profile}")
            continue
        if args.dry_run:
            print(f"dry-run: would refresh custom profile {profile}")
            continue

        (pdir / "SOUL.md").write_text(textwrap.dedent(custom_soul(spec)).strip() + "\n", encoding="utf-8")
        seed_auth_if_missing(args.hermes_home, pdir, args.no_copy_auth)
        memories = pdir / "memories"
        memories.mkdir(exist_ok=True)
        (memories / "MEMORY.md").write_text(textwrap.dedent(custom_memory(spec)).strip() + "\n", encoding="utf-8")
        (pdir / "CUSTOM_AGENT_SPEC.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        cfg_path = pdir / "config.yaml"
        cfg = load_yaml(cfg_path)
        cfg.setdefault("skills", {})
        external_dirs = gbrain_external_dirs(args)
        cfg["skills"]["external_dirs"] = merged_external_dirs(
            cfg["skills"].get("external_dirs"),
            external_dirs,
            [gbrain_skills_dir(args)],
        )
        skill_dirs = [args.hermes_home / "skills"] + [Path(path) for path in cfg["skills"]["external_dirs"]]
        skills = list_skill_names(pdir, skill_dirs)
        if spec.get("allow_all_skills"):
            cfg["skills"]["disabled"] = []
        else:
            allowed = allowed_skills_for_agent(profile, spec)
            cfg["skills"]["disabled"] = [s for s in skills if s not in allowed]
        cfg.setdefault("delegation", {})
        cfg["delegation"].pop("default_toolsets", None)
        cfg.setdefault("platform_toolsets", {})
        cfg["platform_toolsets"].setdefault("cli", [])
        if "delegation" not in cfg["platform_toolsets"]["cli"]:
            cfg["platform_toolsets"]["cli"].append("delegation")
        cfg.setdefault("discord", {})
        cfg["discord"]["require_mention"] = True
        cfg["discord"]["free_response_channels"] = ""
        cfg["discord"]["channel_prompts"] = {}
        dump_yaml(cfg_path, cfg)

        upsert_env(pdir / ".env", {"WIKI_PATH": str(args.wiki_path)}, {})


def discord_setup_doc() -> str:
    return """\
# Discord #agent-proposals Setup

The default Hermes profile owns the Discord proposal intake channel for the Hermes OPC Agent Team.

Fill these in the default `.env` before starting the default gateway:

```bash
DISCORD_BOT_TOKEN=<coordinator-bot-token>
DISCORD_ALLOWED_USERS=<your-discord-user-id>
DISCORD_HOME_CHANNEL=<agent-proposals-channel-id>
DISCORD_FREE_RESPONSE_CHANNELS=<agent-proposals-channel-id>
DISCORD_HOME_CHANNEL_NAME=#agent-proposals
```

When using the Hermes target, run the initializer with `--discord-channel-id` so the default `config.yaml` receives the channel prompt. Placeholder channel IDs are not written into default config.

After filling real values:

```bash
hermes gateway install
hermes gateway start
hermes gateway status
```

In Discord, run `/sethome` inside `#agent-proposals` once the bot is present.

Policy: only default/coordinator-primary connects to Discord. Researcher, writer, and builder remain internal unless a separate bot and channel policy are intentionally added.
"""


def write_if_missing(path: Path, content: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        print(f"exists: {path}")
        return
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    print(f"wrote: {path}")


def init_wiki(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    if args.dry_run:
        print(f"dry-run: would initialize wiki at {args.wiki_path}")
        return
    today = _dt.date.today().isoformat()
    wiki = args.wiki_path
    for rel in [
        "raw/articles",
        "raw/papers",
        "raw/transcripts",
        "raw/assets",
        "entities",
        "concepts",
        "comparisons",
        "queries",
        "projects",
        "decisions",
        "outputs",
        "inbox",
        "_meta",
        "_archive",
    ]:
        (wiki / rel).mkdir(parents=True, exist_ok=True)

    write_if_missing(wiki / "SCHEMA.md", f"""\
# Wiki Schema

## Domain
Hermes OPC Agent Team 的共享记忆系统：核心 Profile、自定义 peer Profile、Subagent 汇报、项目空间、提案、决策、交付、复盘和可复用方法论。

## Conventions
- File names: lowercase, hyphens, no spaces.
- Every maintained page starts with YAML frontmatter.
- Use `[[wikilinks]]` for cross references when the target page exists.
- Raw source files under `raw/` are immutable; corrections go in maintained pages.
- Project state belongs in `projects/`, decisions in `decisions/`, finished deliverables in `outputs/`.
- Subagent reports are compact handoffs; durable summaries belong in maintained pages.
- Custom Profiles are peer Profiles and are registered in `entities/custom-profiles.md`.
- Every new maintained page must be added to `index.md`.
- Every action must be appended to `log.md`.

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | project | decision | output | summary
tags: []
sources: []
---
```

## Tag Taxonomy
- agent-team: profile, subagent, coordination, role-boundary
- memory: wiki, memory-boundary, obsidian, source
- workflow: proposal, routing, handoff, review, delivery
- project: status, milestone, decision, retrospective
- engineering: implementation, testing, automation, gateway
- content: writing, research, publishing, synthesis

Rule: add a tag to this taxonomy before using it on a maintained page.
""", args.force_wiki)

    write_if_missing(wiki / "index.md", f"""\
# Wiki Index

> Content catalog for the Hermes OPC Agent Team shared memory.
> Last updated: {today} | Total maintained pages: 5

## Concepts
- [[opc-agent-team]] — Default-as-coordinator Hermes team model for coordinating long-running work.
- [[shared-wiki-memory]] — Shared memory layer that keeps project state out of individual Profile memory.
- [[subagent-reporting-protocol]] — Compact report contract for temporary Subagents.

## Entities
- [[custom-profiles]] — Registered user-defined peer Profiles and their routing triggers.

## Projects
- [[opc-agent-team-operating-model]] — Initial operating model for core Profiles, custom Profiles, Wiki, Discord proposal intake, and Subagent delegation.

## Comparisons

## Queries

## Decisions

## Outputs
""", args.force_wiki)

    write_if_missing(wiki / "log.md", f"""\
# Wiki Log

> Chronological record of all wiki actions.
> Format: `## [YYYY-MM-DD] action | subject`
> Actions: ingest, update, query, lint, create, archive, delete.

## [{today}] create | Wiki initialized or refreshed
- Domain: Hermes OPC Agent Team shared memory.
- Created/refreshed structure and core pages.
- Subagent reporting protocol included.
- Custom Profile registry included.
""", args.force_wiki)

    write_if_missing(wiki / "concepts/subagent-reporting-protocol.md", SUBAGENT_PAGE.format(date=today), args.force_wiki)
    write_if_missing(wiki / "entities/custom-profiles.md", custom_profiles_page(custom_specs, today), args.force_wiki)
    write_if_missing(wiki / "concepts/opc-agent-team.md", f"""\
---
title: OPC Agent Team
created: {today}
updated: {today}
type: concept
tags: [profile, subagent, coordination, role-boundary]
sources: [raw/articles/knoyee-hermes-opc-multi-profile-2026-04-29.md]
---

# OPC Agent Team

OPC Agent Team 是一套把 Hermes 拆成多个长期 Profile 的工作系统。目标不是多开聊天窗口，而是建立清晰的角色边界、记忆边界和交付流程。

## Roles
- Default/coordinator-primary: 定义目标、拆分任务、路由角色、汇总结果、维护 [[shared-wiki-memory]]。
- Researcher: 收集证据、交叉验证、标注不确定性。
- Writer: 把可靠材料组织成清晰内容。
- Builder: 把计划落地成可运行、可测试、可交付的系统。

## Subagents
Subagent 是临时工作单元，只处理局部问题。它不需要长期人格，也不写长期 memory。它按 [[subagent-reporting-protocol]] 汇报给唯一 owning Profile。

## Custom Profiles
User-defined Profiles are peer Profiles registered in [[custom-profiles]]. They serve specialized user needs and can be routed directly by coordinator.

## Boundary Rule
同一套长期 Profile 可以服务多个 Project；不要为每个项目复制一套 Profile。项目状态放进 Wiki，角色经验放进对应 Profile memory。
""", args.force_wiki)

    write_if_missing(wiki / "concepts/shared-wiki-memory.md", f"""\
---
title: Shared Wiki Memory
created: {today}
updated: {today}
type: concept
tags: [wiki, memory-boundary, obsidian, source]
sources: [raw/articles/knoyee-hermes-opc-multi-profile-2026-04-29.md]
---

# Shared Wiki Memory

Shared Wiki Memory 是 Hermes OPC Agent Team 的共享文档层。它解决多 Profile 之间记忆不相通的问题，同时避免把项目状态写进个人 Profile memory。

## What Belongs Here
- 项目状态、任务进度、交接单。
- 决策记录、复盘、最终产出。
- 研究材料、来源摘要、通用方法论。
- Subagent 报告的 durable summary。
- Custom Profile routing metadata and durable summaries.
- Discord `#agent-proposals` 进入的提案卡。

## What Does Not Belong Here
- API key、token、密码等密钥。
- 纯临时思考和未整理草稿。
- 可以轻易从项目文件重新发现的低价值信息。

## Operating Link
[[opc-agent-team]] 使用本 Wiki 作为团队共享记忆。每个 Profile 通过同一个 `WIKI_PATH` 读写这里。
""", args.force_wiki)

    write_if_missing(wiki / "projects/opc-agent-team-operating-model.md", f"""\
---
title: OPC Agent Team Operating Model
created: {today}
updated: {today}
type: project
tags: [proposal, routing, handoff, delivery]
sources: [raw/articles/knoyee-hermes-opc-multi-profile-2026-04-29.md]
---

# OPC Agent Team Operating Model

## Current Configuration
- Long-term Hermes Profiles: default/coordinator-primary, researcher, writer, builder.
- Custom peer Profiles: see [[custom-profiles]].
- Shared memory: [[shared-wiki-memory]] at `WIKI_PATH`.
- Proposal intake: Discord `#agent-proposals`, owned by default/coordinator-primary.
- Temporary execution: Subagents are used only for bounded local tasks and report through [[subagent-reporting-protocol]].

## Default Flow
1. Default/coordinator-primary turns user input into a proposal card.
2. Default/coordinator-primary routes to one primary owner: a core Profile, a custom Profile, or bounded temporary Subagent work.
3. The owning Profile or temporary Subagent returns a compact deliverable.
4. Default/coordinator-primary merges output, checks boundaries, and records durable state in Wiki.

## Proposal Card
- Goal:
- Background:
- Constraints:
- Deliverable:
- Suggested route:
- Next checkpoint:

## Memory Boundary
Profile memory stores durable role lessons. Project state, progress, decisions, Subagent summaries, and outputs stay in this Wiki.
""", args.force_wiki)

    write_if_missing(wiki / "raw/articles/knoyee-hermes-opc-multi-profile-2026-04-29.md", f"""\
---
title: Hermes multi-profile OPC article source note
created: {today}
updated: {today}
type: summary
tags: [source, profile, wiki]
sources: [https://x.com/knoyee_/status/2049414174783193349]
---

# Hermes Multi-Profile OPC Article Source Note

Source: https://x.com/knoyee_/status/2049414174783193349

Published: 2026-04-29.

The article argues for organizing Hermes as a small OPC-style agent team: long-term Profiles handle stable roles, Subagents handle temporary local tasks, Projects hold work context, and a shared Wiki synchronizes durable state across Profiles.

Operational takeaways:
- Use Profile boundaries to reduce hallucination, memory pollution, and role confusion.
- Keep project state out of `SOUL.md`, `USER.md`, `.env`, and role memory.
- Use a shared Wiki for project progress, decisions, research material, outputs, and reusable methods.
- A practical Hermes model is default/coordinator-primary plus researcher, writer, and builder.
""", args.force_wiki)


def write_generated(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    print(f"wrote: {path}")


def write_generated_json(path: Path, data: Any) -> None:
    write_generated(path, json.dumps(data, ensure_ascii=False, indent=2))


def home_relative(path: Path) -> str:
    expanded = path.expanduser()
    home = Path.home()
    try:
        return "~/" + str(expanded.relative_to(home))
    except ValueError:
        return str(expanded)


def openclaw_agent_title(name: str) -> str:
    return "OPC " + " ".join(part.capitalize() for part in name.split("-"))


def openclaw_workspace_dir(package: Path, name: str) -> Path:
    return package / "workspaces" / name


def openclaw_agent_dir(package: Path, name: str) -> Path:
    return package / "agent-dirs" / name


def openclaw_skill_extra_dirs(args: argparse.Namespace) -> list[str]:
    dirs: list[Path] = []
    if args.dependencies["gstack"]["openclaw_skills_present"]:
        dirs.append(gstack_openclaw_skills_dir(args))
    elif args.dependencies["gstack"]["openclaw_source_present"]:
        dirs.append(args.gstack_root / "openclaw" / "skills")
    if args.dependencies["gbrain"]["skills_present"]:
        dirs.append(gbrain_skills_dir(args))
    return list(dict.fromkeys(home_relative(path) for path in dirs))


def openclaw_all_selected_skills(custom_specs: list[dict[str, Any]]) -> list[str]:
    names: set[str] = set()
    for profile in PROFILES:
        names.update(allowed_skills_for_agent(profile, target="openclaw"))
    for spec in custom_specs:
        names.update(allowed_skills_for_agent(spec["name"], spec, target="openclaw"))
    return sorted(names)


def openclaw_workspace_agents_md(name: str, summary: str, allowed_skills: list[str], wiki_path: Path) -> str:
    skills_text = markdown_list(allowed_skills) if allowed_skills else "- Use the runtime's available skills only when they match this agent's role."
    return f"""\
# {name} OpenClaw Workspace

You are `{name}` in the OPC Agent Team.

## Role
{summary}

## Shared Wiki
Use this shared durable memory path:

```text
{wiki_path}
```

Project state, decisions, handoffs, and Subagent summaries belong in the shared Wiki, not in chat history or long-term role memory.

## Skills
{skills_text}

## Subagents
- Spawn temporary Subagents only for bounded, context-heavy, independent work.
- A temporary Subagent reports back only to `{name}`.
- Compress Subagent output before writing durable summaries to the Wiki.
"""


def openclaw_identity_md(name: str, summary: str) -> str:
    return f"""\
# IDENTITY.md

name: {openclaw_agent_title(name)}
theme: {summary}
"""


def openclaw_agent_markdown(name: str, summary: str, soul_text: str, memory_text: str, allowed_skills: list[str], wiki_path: Path) -> str:
    return f"""\
# {name} OPC Agent Spec

Target runtime: OpenClaw reference package plus `openclaw.config.patch.json5`.

## Role Summary
{summary}

## Shared Wiki
Use this shared durable memory path:

```text
{wiki_path}
```

Project state, decisions, Subagent summaries, and deliverables belong in the shared Wiki, not in long-term role memory.

## Suggested Skills
{markdown_list(allowed_skills)}

## System Prompt
{textwrap.dedent(soul_text).strip()}

## Long-Term Role Memory Seed
{textwrap.dedent(memory_text).strip()}
"""


def openclaw_custom_agent_markdown(spec: dict[str, Any], wiki_path: Path) -> str:
    summary = f"用户自定义 peer Agent，mission: {spec['mission']}"
    return openclaw_agent_markdown(
        spec["name"],
        summary,
        custom_soul(spec),
        custom_memory(spec),
        sorted(allowed_skills_for_agent(spec["name"], spec, target="openclaw")),
        wiki_path,
    )


def openclaw_agent_records(custom_specs: list[dict[str, Any]], wiki_path: Path, dependencies: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for profile in PROFILES:
        bundle = skill_distribution_for_agent(profile, target="openclaw")
        records.append({
            "name": profile,
            "kind": "core-agent",
            "role_summary": CORE_PROFILE_SUMMARY[profile],
            "prompt_file": f"agents/{profile}.md",
            "workspace_dir": f"workspaces/{profile}",
            "allowed_skills": sorted(allowed_skills_for_agent(profile, target="openclaw")),
            **bundle,
            "dependency_notes": dependency_notes_for_agent(profile, dependencies, target="openclaw"),
            "wiki_path": str(wiki_path),
            "subagent_report_target": profile,
        })
    for spec in custom_specs:
        bundle = skill_distribution_for_agent(spec["name"], target="openclaw")
        records.append({
            "name": spec["name"],
            "kind": "custom-peer-agent",
            "mission": spec["mission"],
            "prompt_file": f"agents/{spec['name']}.md",
            "workspace_dir": f"workspaces/{spec['name']}",
            "allowed_skills": sorted(allowed_skills_for_agent(spec["name"], spec, target="openclaw")),
            **bundle,
            "dependency_notes": dependency_notes_for_agent(spec["name"], dependencies, target="openclaw"),
            "routing_triggers": spec["routing_triggers"],
            "wiki_scope": spec["wiki_scope"],
            "discord_channel_name": spec["discord_channel_name"],
            "discord_channel_id": spec["discord_channel_id"],
            "wiki_path": str(wiki_path),
            "subagent_report_target": spec["name"],
        })
    return records


def openclaw_channel_routes(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> dict[str, Any]:
    channels: list[dict[str, str]] = [{
        "channel_name": "#agent-proposals",
        "channel_id": args.discord_channel_id or "",
        "routes_to": "coordinator",
        "prompt": textwrap.dedent(DISCORD_PROMPT).strip(),
    }]
    for spec in custom_specs:
        channels.append({
            "channel_name": spec["discord_channel_name"],
            "channel_id": spec["discord_channel_id"],
            "routes_to": spec["name"],
            "prompt": textwrap.dedent(custom_channel_prompt(spec)).strip(),
        })
    return {
        "policy": "Use one coordinator-owned Discord bot token; route distinct channels by channel prompt.",
        "token_owner": "coordinator",
        "token_env_var": "DISCORD_BOT_TOKEN",
        "allowed_users_env_var": "DISCORD_ALLOWED_USERS",
        "channels": channels,
    }


def openclaw_route_bindings(custom_specs: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    if args.discord_channel_id:
        bindings.append({
            "type": "route",
            "agentId": "coordinator",
            "comment": "OPC proposal intake channel.",
            "match": {
                "channel": "discord",
                "peer": {"kind": "channel", "id": args.discord_channel_id},
            },
        })
    for spec in custom_specs:
        channel_id = spec.get("discord_channel_id") or ""
        if not channel_id:
            continue
        bindings.append({
            "type": "route",
            "agentId": spec["name"],
            "comment": f"OPC custom peer Agent channel for {spec['name']}.",
            "match": {
                "channel": "discord",
                "peer": {"kind": "channel", "id": channel_id},
            },
        })
    return bindings


def openclaw_discord_channel_config(prompt: str, skills: list[str], args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {
        "requireMention": False,
        "systemPrompt": prompt,
        "skills": skills,
    }
    if args.discord_user_id:
        config["users"] = [args.discord_user_id]
    return config


def openclaw_discord_config(custom_specs: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any] | None:
    channel_ids = [args.discord_channel_id] if args.discord_channel_id else []
    channel_ids.extend(spec.get("discord_channel_id") or "" for spec in custom_specs)
    channel_ids = [channel_id for channel_id in channel_ids if channel_id]
    if not channel_ids:
        return None
    config: dict[str, Any] = {
        "enabled": True,
        "token": {"source": "env", "provider": "default", "id": "DISCORD_BOT_TOKEN"},
        "groupPolicy": "allowlist",
    }
    if args.discord_user_id:
        config["allowFrom"] = [args.discord_user_id]
    if args.discord_guild_id:
        channels: dict[str, Any] = {}
        if args.discord_channel_id:
            channels[args.discord_channel_id] = openclaw_discord_channel_config(
                textwrap.dedent(DISCORD_PROMPT).strip(),
                sorted(allowed_skills_for_agent("coordinator", target="openclaw")),
                args,
            )
        for spec in custom_specs:
            channel_id = spec.get("discord_channel_id") or ""
            if not channel_id:
                continue
            channels[channel_id] = openclaw_discord_channel_config(
                textwrap.dedent(custom_channel_prompt(spec)).strip(),
                sorted(allowed_skills_for_agent(spec["name"], spec, target="openclaw")),
                args,
            )
        config["guilds"] = {args.discord_guild_id: {"channels": channels}}
    return config


def openclaw_config_patch(package: Path, custom_specs: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    agents: list[dict[str, Any]] = []
    for profile in PROFILES:
        skills = sorted(allowed_skills_for_agent(profile, target="openclaw"))
        entry: dict[str, Any] = {
            "id": profile,
            "name": openclaw_agent_title(profile),
            "workspace": home_relative(openclaw_workspace_dir(package, profile)),
            "agentDir": home_relative(openclaw_agent_dir(package, profile)),
            "identity": {
                "name": openclaw_agent_title(profile),
                "theme": CORE_PROFILE_SUMMARY[profile],
            },
            "subagents": {"allowAgents": [profile]},
        }
        if profile == "coordinator":
            entry["default"] = True
        if skills:
            entry["skills"] = skills
        agents.append(entry)
    for spec in custom_specs:
        skills = sorted(allowed_skills_for_agent(spec["name"], spec, target="openclaw"))
        entry = {
            "id": spec["name"],
            "name": openclaw_agent_title(spec["name"]),
            "workspace": home_relative(openclaw_workspace_dir(package, spec["name"])),
            "agentDir": home_relative(openclaw_agent_dir(package, spec["name"])),
            "identity": {
                "name": openclaw_agent_title(spec["name"]),
                "theme": spec["mission"],
            },
            "subagents": {"allowAgents": [spec["name"]]},
        }
        if skills:
            entry["skills"] = skills
        agents.append(entry)

    patch: dict[str, Any] = {
        "agents": {"list": agents},
        "skills": {
            "load": {"extraDirs": openclaw_skill_extra_dirs(args)},
            "entries": {name: {"enabled": True} for name in openclaw_all_selected_skills(custom_specs)},
        },
    }
    if args.dependencies["gbrain"]["openclaw_plugin_present"]:
        patch["plugins"] = {"load": {"paths": [home_relative(args.gbrain_root)]}}
    bindings = openclaw_route_bindings(custom_specs, args)
    if bindings:
        patch["bindings"] = bindings
    discord = openclaw_discord_config(custom_specs, args)
    if discord:
        patch["secrets"] = {
            "providers": {
                "default": {
                    "source": "env",
                    "allowlist": ["DISCORD_BOT_TOKEN"],
                },
            },
        }
        patch["channels"] = {"discord": discord}
    return patch


def openclaw_import_doc(package: Path, wiki_path: Path) -> str:
    return f"""\
# OPC Team OpenClaw Package

This directory is a non-invasive OpenClaw package. It does not edit `.openclaw/openclaw.json`.

## Files
- `manifest.json`: package metadata.
- `dependencies.json`: detected GStack/GBrain dependency state and install hints.
- `agent-skill-map.json`: role-based OpenClaw skill distribution matrix.
- `agents.json`: structured agent registry.
- `agents/*.md`: prompt and role-memory seeds for each core or custom Agent.
- `agent-dirs/*/`: real OpenClaw per-agent `agentDir` folders.
- `workspaces/*/`: real OpenClaw per-agent workspace bootstrap files.
- `openclaw.config.patch.json5`: OpenClaw `openclaw.json`-compatible config patch.
- `routing-table.md`: coordinator routing table.
- `discord-channel-routing.json`: one-token, multi-channel routing policy.
- `subagent-reporting.md`: temporary Subagent report contract.
- `wiki-template/`: seed Wiki pages for the shared memory model.

## Integration Pattern
1. Keep the shared Wiki at `{wiki_path}`.
2. Review and merge `openclaw.config.patch.json5` into `~/.openclaw/openclaw.json`.
3. Keep Discord token ownership centralized in the coordinator process.
4. Map channels from `discord-channel-routing.json`; custom Agents get their own channels but not their own bot token by default.
5. Temporary Subagents report only to the owning Agent named in `agents.json`.

Generated package path:

```text
{package}
```

No secrets are written into this package.
"""


def init_openclaw_package(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    package = openclaw_package_dir(args.openclaw_home)
    if args.dry_run:
        print(f"dry-run: would initialize OpenClaw package at {package}")
        return
    today = _dt.date.today().isoformat()
    generated_at = _dt.datetime.now().isoformat(timespec="seconds")
    (package / "agents").mkdir(parents=True, exist_ok=True)
    (package / "agent-dirs").mkdir(parents=True, exist_ok=True)
    (package / "workspaces").mkdir(parents=True, exist_ok=True)
    (package / "wiki-template").mkdir(parents=True, exist_ok=True)

    records = openclaw_agent_records(custom_specs, args.wiki_path, args.dependencies)
    manifest = {
        "name": "opc-team",
        "target": "openclaw",
        "generated_at": generated_at,
        "openclaw_home": str(args.openclaw_home),
        "wiki_path": str(args.wiki_path),
        "core_agents": list(PROFILES),
        "custom_agents": [spec["name"] for spec in custom_specs],
        "compatibility_mode": "non-invasive package; openclaw.json is not modified",
    }
    write_generated_json(package / "manifest.json", manifest)
    write_generated_json(package / "dependencies.json", args.dependencies)
    write_generated_json(package / "agent-skill-map.json", agent_skill_map(custom_specs, target="openclaw"))
    write_generated_json(package / "agents.json", records)
    write_generated_json(package / "openclaw.config.patch.json5", openclaw_config_patch(package, custom_specs, args))
    write_generated_json(package / "discord-channel-routing.json", openclaw_channel_routes(args, custom_specs))
    write_generated(package / "routing-table.md", routing_table(custom_specs))
    write_generated(package / "subagent-reporting.md", SUBAGENT_PAGE.format(date=today))
    write_generated(package / "OPENCLAW_IMPORT.md", openclaw_import_doc(package, args.wiki_path))
    write_generated(package / ".env.example", f"""\
WIKI_PATH={args.wiki_path}
DISCORD_BOT_TOKEN=<coordinator-bot-token>
DISCORD_ALLOWED_USERS=<your-discord-user-id>
DISCORD_HOME_CHANNEL=<agent-proposals-channel-id>
DISCORD_FREE_RESPONSE_CHANNELS=<agent-proposals-channel-id>
DISCORD_HOME_CHANNEL_NAME=#agent-proposals
""")

    for profile in PROFILES:
        write_generated(
            package / "agents" / f"{profile}.md",
            openclaw_agent_markdown(
                profile,
                CORE_PROFILE_SUMMARY[profile],
                SOUL[profile],
                MEMORY[profile],
                sorted(allowed_skills_for_agent(profile, target="openclaw")),
                args.wiki_path,
            ),
        )
        allowed = sorted(allowed_skills_for_agent(profile, target="openclaw"))
        workspace = openclaw_workspace_dir(package, profile)
        agent_dir = openclaw_agent_dir(package, profile)
        write_generated(workspace / "AGENTS.md", openclaw_workspace_agents_md(profile, CORE_PROFILE_SUMMARY[profile], allowed, args.wiki_path))
        write_generated(agent_dir / "AGENTS.md", openclaw_workspace_agents_md(profile, CORE_PROFILE_SUMMARY[profile], allowed, args.wiki_path))
        write_generated(agent_dir / "SOUL.md", SOUL[profile])
        write_generated(agent_dir / "MEMORY.md", MEMORY[profile])
        write_generated(agent_dir / "IDENTITY.md", openclaw_identity_md(profile, CORE_PROFILE_SUMMARY[profile]))
    for spec in custom_specs:
        write_generated(package / "agents" / f"{spec['name']}.md", openclaw_custom_agent_markdown(spec, args.wiki_path))
        allowed = sorted(allowed_skills_for_agent(spec["name"], spec, target="openclaw"))
        summary = f"用户自定义 peer Agent，mission: {spec['mission']}"
        workspace = openclaw_workspace_dir(package, spec["name"])
        agent_dir = openclaw_agent_dir(package, spec["name"])
        write_generated(workspace / "AGENTS.md", openclaw_workspace_agents_md(spec["name"], summary, allowed, args.wiki_path))
        write_generated(agent_dir / "AGENTS.md", openclaw_workspace_agents_md(spec["name"], summary, allowed, args.wiki_path))
        write_generated(agent_dir / "SOUL.md", custom_soul(spec))
        write_generated(agent_dir / "MEMORY.md", custom_memory(spec))
        write_generated(agent_dir / "IDENTITY.md", openclaw_identity_md(spec["name"], spec["mission"]))

    write_generated(package / "wiki-template" / "SCHEMA.md", f"""\
# Wiki Schema

Domain: OPC Agent Team shared memory for Hermes or OpenClaw runtimes.

- Core Agents: coordinator, researcher, writer, builder.
- Custom Agents: peer specialists registered in `custom-profiles.json`.
- Durable state goes into the shared Wiki at `{args.wiki_path}`.
- Secrets never go into Wiki, prompt files, generated manifests, or channel routing files.
- Temporary Subagents are disposable and report to exactly one owning Agent.
""")
    write_generated(package / "wiki-template" / "index.md", f"""\
# OPC Team Wiki Index

Generated: {today}

## Core Concepts
- OPC Agent Team
- Shared Wiki Memory
- Subagent Reporting Protocol

## Custom Agents
See `custom-profiles.json` and `agents.json`.
""")
    write_generated(package / "wiki-template" / "log.md", f"""\
# Wiki Log

## [{today}] create | OpenClaw OPC package generated
- Package: `{package}`
- Shared Wiki path: `{args.wiki_path}`
""")


def maybe_start_gateway(args: argparse.Namespace) -> None:
    if not args.start_gateway:
        return
    if not (args.discord_bot_token and args.discord_user_id and args.discord_channel_id):
        raise SystemExit("--start-gateway requires --discord-bot-token, --discord-user-id, and --discord-channel-id")
    if args.dry_run:
        print("dry-run: would install/start default Hermes gateway")
        return
    env = command_env(args.hermes_home)
    run(["hermes", "gateway", "install"], env=env, check=False)
    run(["hermes", "gateway", "start"], env=env, check=False)


def run_checks(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    if args.dry_run:
        return
    env = command_env(args.hermes_home)
    run(["hermes", "profile", "list"], env=env, check=False)
    run(["hermes", "gateway", "status"], env=env, check=False)
    if args.run_chat_checks:
        run(["hermes", "chat", "-Q", "-q", "用一句话说明你的职责边界。"], env=env, check=False)
        for profile in list(HERMES_SPECIALIST_PROFILES) + [spec["name"] for spec in custom_specs]:
            run([profile, "chat", "-Q", "-q", "用一句话说明你的职责边界。"], env=env, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["hermes", "openclaw"], default="hermes", help="runtime/configuration target")
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--openclaw-home", type=Path, default=Path.home() / ".openclaw")
    parser.add_argument("--dependency-mode", choices=["prompt", "strict", "off"], default="prompt", help="how to handle missing GStack/GBrain dependencies")
    parser.add_argument("--gstack-root", type=Path, help="GStack checkout root; defaults to ~/gstack")
    parser.add_argument("--gbrain-root", type=Path, help="GBrain checkout root; defaults to ~/gbrain")
    parser.add_argument("--wiki-path", type=Path, help="absolute shared Wiki path; overrides vault selection")
    parser.add_argument("--vault-path", type=Path, help="shared vault root used with --wiki-folder-name")
    parser.add_argument("--wiki-folder-name", default=DEFAULT_WIKI_FOLDER_NAME, help="relative folder inside the selected vault; default '.' means the vault root")
    parser.add_argument("--select-vault", action="store_true", help="interactively choose the shared vault before initializing")
    parser.add_argument("--discord-channel-id")
    parser.add_argument("--discord-guild-id", help="Discord guild/server ID used by the OpenClaw config patch")
    parser.add_argument("--discord-user-id")
    parser.add_argument("--discord-bot-token")
    parser.add_argument("--custom-profile-spec", action="append", help="JSON file containing one custom agent spec or a list of specs")
    parser.add_argument("--custom-profile-json", action="append", help="Inline JSON object for one custom peer agent")
    parser.add_argument("--custom-profile-preset", action="append", help="Built-in custom agent preset: growth-agent or secretary")
    parser.add_argument("--no-copy-auth", action="store_true", help="do not seed missing Hermes profile auth.json from the default Hermes home")
    parser.add_argument("--force-wiki", action="store_true", help="overwrite seed Wiki files")
    parser.add_argument("--start-gateway", action="store_true", help="install and start the default Hermes gateway after real Discord values are supplied")
    parser.add_argument("--run-chat-checks", action="store_true", help="spend model calls to check each role responds with its boundary")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.hermes_home = args.hermes_home.expanduser()
    args.openclaw_home = args.openclaw_home.expanduser()
    args.gstack_root_explicit = args.gstack_root is not None
    args.gbrain_root_explicit = args.gbrain_root is not None
    args.gstack_root = (args.gstack_root or Path.home() / "gstack").expanduser()
    args.gbrain_root = (args.gbrain_root or Path.home() / "gbrain").expanduser()
    args.wiki_path = resolve_wiki_path(args)
    args.dependencies = check_dependencies(args)
    requested_custom_specs = load_custom_specs(args)

    if args.target == "hermes":
        validate_openai_codex_oauth(args)
        create_missing_profiles(args.hermes_home, args.dry_run, [])
        custom_specs = merge_custom_registry(args.hermes_home, requested_custom_specs, args.dry_run)
        create_missing_profiles(args.hermes_home, args.dry_run, custom_specs)
        refresh_profiles(args, custom_specs)
        init_wiki(args, custom_specs)
        maybe_start_gateway(args)
        run_checks(args, custom_specs)
        print("Hermes OPC team initialization complete.")
        print(f"Hermes home: {args.hermes_home}")
    else:
        custom_specs = merge_openclaw_custom_registry(args.openclaw_home, requested_custom_specs, args.dry_run)
        init_openclaw_package(args, custom_specs)
        init_wiki(args, custom_specs)
        print("OpenClaw OPC team package initialization complete.")
        print(f"OpenClaw home: {args.openclaw_home}")
        print(f"Package path: {openclaw_package_dir(args.openclaw_home)}")
    print(f"Wiki path: {args.wiki_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
