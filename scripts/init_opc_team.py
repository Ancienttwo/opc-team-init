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
            "Do not change product direction without coordinator approval",
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


MEMORY = {
    "coordinator": """\
Coordinator 的长期经验：
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
Suggested route must pick one primary owner from coordinator, researcher, writer, builder, or temporary subagent.
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
- Coordinator: routing, status, integration, decisions.
- Researcher: evidence, sources, contradictions, uncertainty.
- Writer: outlines, drafts, editorial variants.
- Builder: patches, tests, implementation risks, review findings.
- Custom Profile: specialized work owned by that registered custom Profile.

## Report Shape

```markdown
## Subagent Report

Target: coordinator | researcher | writer | builder | <custom-profile-name>
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
    return profile_dir(hermes_home, "coordinator") / CUSTOM_REGISTRY_NAME


def routing_table_path(hermes_home: Path) -> Path:
    return profile_dir(hermes_home, "coordinator") / ROUTING_TABLE_NAME


def openclaw_package_dir(openclaw_home: Path) -> Path:
    return openclaw_home / OPENCLAW_PACKAGE_DIRNAME


def openclaw_registry_path(openclaw_home: Path) -> Path:
    return openclaw_package_dir(openclaw_home) / "custom-profiles.json"


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
    if normalized in PROFILES:
        raise SystemExit(f"Custom profile {normalized!r} conflicts with a core Profile")
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
            "Do not bypass coordinator routing for cross-profile work",
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
    return read_custom_registry_file(path)


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
    for profile in list(PROFILES) + [spec["name"] for spec in custom_specs]:
        pdir = profile_dir(hermes_home, profile)
        if pdir.exists():
            print(f"exists: {pdir}")
            continue
        if dry_run:
            print(f"dry-run: would create profile {profile}")
            continue
        run([hermes, "profile", "create", profile, "--clone"], env=env)


def list_skill_names(profile: Path) -> list[str]:
    names: set[str] = set()
    for skill_md in (profile / "skills").rglob("SKILL.md"):
        match = re.search(r"^name:\s*(.+?)\s*$", skill_md.read_text(encoding="utf-8", errors="ignore"), re.M)
        if match:
            names.add(match.group(1).strip().strip("\"'"))
    return sorted(names)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        ruby = shutil.which("ruby")
        if not ruby:
            raise SystemExit("Need PyYAML or Ruby stdlib YAML to update config.yaml")
        proc = subprocess.run(
            [ruby, "-ryaml", "-rjson", "-e", "puts JSON.generate(YAML.load_file(ARGV[0]) || {})", str(path)],
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
        lines.append("# Discord #agent-proposals wiring. Fill before starting coordinator gateway.")
        for key, value in missing_placeholders:
            lines.append(f"# {key}={value}")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def custom_soul(spec: dict[str, Any]) -> str:
    name = spec["name"]
    return f"""\
# {name} Profile

你是 Hermes OPC Agent Team 的用户自定义专门 Agent：`{name}`。你与 coordinator、researcher、writer、builder 平级，专门服务用户的特别需求。

## Mission
{spec["mission"]}

## 核心职责
{markdown_list(spec["responsibilities"])}

## Subagent 规则
- 当任务独立、上下文重、适合并行时，可以 spawn temporary Subagent。
- 你 spawn 的 Subagent 只服务 `{name}`，必须向 `{name}` 汇报，不直接汇报给四个核心 Profile。
- 你负责压缩、审查和合并 Subagent 报告，再按需交给 coordinator 或写入共享 Wiki。

## 边界
{markdown_list(spec["boundaries"])}

## Wiki Scope
{spec["wiki_scope"]}

## 工作方式
- 默认用中文汇报。
- 先判断任务是否属于 `{name}` 的 mission；跨边界任务交还 coordinator 路由。
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
跨出职责边界时交还 coordinator 路由，不擅自替其他 Profile 做最终决策。
"""


def custom_channel_prompt(spec: dict[str, Any]) -> str:
    return f"""\
This Discord channel belongs to custom Hermes Profile `{spec["name"]}`.
Use the single coordinator-owned Discord bot token, but route this channel's work to `{spec["name"]}`.
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
        "- coordinator: goals, planning, routing, integration, decisions.",
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
        "Custom Profiles are user-defined peer Hermes Profiles. They are not children of coordinator, researcher, writer, or builder.",
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


def refresh_profiles(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    channel_id = args.discord_channel_id or PLACEHOLDER_CHANNEL
    for profile in PROFILES:
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
        memory_text = coordinator_memory(custom_specs) if profile == "coordinator" else textwrap.dedent(MEMORY[profile]).strip() + "\n"
        (memories / "MEMORY.md").write_text(memory_text, encoding="utf-8")

        cfg_path = pdir / "config.yaml"
        cfg = load_yaml(cfg_path)
        skills = list_skill_names(pdir)
        cfg.setdefault("skills", {})
        cfg["skills"]["disabled"] = [s for s in skills if s not in ALLOWED_SKILLS[profile]]
        cfg.setdefault("delegation", {})
        cfg["delegation"].setdefault("default_toolsets", ["terminal", "file", "web"])
        cfg.setdefault("platform_toolsets", {})
        cfg["platform_toolsets"].setdefault("cli", [])
        if "delegation" not in cfg["platform_toolsets"]["cli"]:
            cfg["platform_toolsets"]["cli"].append("delegation")

        cfg.setdefault("discord", {})
        cfg["discord"]["require_mention"] = True
        cfg["discord"]["auto_thread"] = True
        cfg["discord"]["reactions"] = True
        if profile == "coordinator":
            free_response, prompts = coordinator_discord_config(args, custom_specs)
            cfg["discord"]["free_response_channels"] = free_response
            cfg["discord"]["channel_prompts"] = prompts
        else:
            cfg["discord"]["free_response_channels"] = ""
            cfg["discord"]["channel_prompts"] = {}
        dump_yaml(cfg_path, cfg)

        env_values = {"WIKI_PATH": str(args.wiki_path)}
        placeholders: dict[str, str] = {}
        if profile == "coordinator":
            free_response, _prompts = coordinator_discord_config(args, custom_specs)
            if args.discord_bot_token:
                env_values["DISCORD_BOT_TOKEN"] = args.discord_bot_token
            if args.discord_user_id:
                env_values["DISCORD_ALLOWED_USERS"] = args.discord_user_id
            if args.discord_channel_id:
                env_values["DISCORD_HOME_CHANNEL"] = args.discord_channel_id
            if PLACEHOLDER_CHANNEL not in free_response:
                env_values["DISCORD_FREE_RESPONSE_CHANNELS"] = free_response
            env_values["DISCORD_HOME_CHANNEL_NAME"] = "#agent-proposals"
            placeholders = {
                "DISCORD_BOT_TOKEN": "<coordinator-bot-token>",
                "DISCORD_ALLOWED_USERS": "<your-discord-user-id>",
                "DISCORD_HOME_CHANNEL": "<agent-proposals-channel-id>",
                "DISCORD_FREE_RESPONSE_CHANNELS": "<agent-proposals-channel-id>",
            }
        upsert_env(pdir / ".env", env_values, placeholders)

        if profile == "coordinator":
            setup = pdir / "DISCORD_AGENT_PROPOSALS_SETUP.md"
            setup.write_text(discord_setup_doc(), encoding="utf-8")
            routing_table_path(args.hermes_home).write_text(routing_table(custom_specs), encoding="utf-8")

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
        skills = list_skill_names(pdir)
        cfg.setdefault("skills", {})
        if spec.get("allow_all_skills"):
            cfg["skills"]["disabled"] = []
        else:
            allowed = set(spec["allowed_skills"]) | {"llm-wiki", "subagent-driven-development"}
            cfg["skills"]["disabled"] = [s for s in skills if s not in allowed]
        cfg.setdefault("delegation", {})
        cfg["delegation"].setdefault("default_toolsets", ["terminal", "file", "web"])
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

This profile owns the Discord proposal intake channel for the Hermes OPC Agent Team.

Fill these in `profiles/coordinator/.env` before starting the coordinator gateway:

```bash
DISCORD_BOT_TOKEN=<coordinator-bot-token>
DISCORD_ALLOWED_USERS=<your-discord-user-id>
DISCORD_HOME_CHANNEL=<agent-proposals-channel-id>
DISCORD_FREE_RESPONSE_CHANNELS=<agent-proposals-channel-id>
DISCORD_HOME_CHANNEL_NAME=#agent-proposals
```

Replace `<AGENT_PROPOSALS_CHANNEL_ID>` in `profiles/coordinator/config.yaml` with the same channel ID if the initializer was run without `--discord-channel-id`.

After filling real values:

```bash
coordinator gateway install
coordinator gateway start
coordinator gateway status
```

In Discord, run `/sethome` inside `#agent-proposals` once the bot is present.

Policy: only coordinator connects to Discord. Researcher, writer, and builder remain internal unless a separate bot and channel policy are intentionally added.
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
- [[opc-agent-team]] — Four-role Hermes team model for coordinating long-running work.
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
- Coordinator: 定义目标、拆分任务、路由角色、汇总结果、维护 [[shared-wiki-memory]]。
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
- Long-term Profiles: coordinator, researcher, writer, builder.
- Custom peer Profiles: see [[custom-profiles]].
- Shared memory: [[shared-wiki-memory]] at `WIKI_PATH`.
- Proposal intake: Discord `#agent-proposals`, owned by coordinator.
- Temporary execution: Subagents are used only for bounded local tasks and report through [[subagent-reporting-protocol]].

## Default Flow
1. Coordinator turns user input into a proposal card.
2. Coordinator routes to one primary owner: a core Profile, a custom Profile, or bounded temporary Subagent work.
3. The owning Profile or temporary Subagent returns a compact deliverable.
4. Coordinator merges output, checks boundaries, and records durable state in Wiki.

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
- A practical four-role model is coordinator, researcher, writer, and builder.
""", args.force_wiki)


def write_generated(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
    print(f"wrote: {path}")


def write_generated_json(path: Path, data: Any) -> None:
    write_generated(path, json.dumps(data, ensure_ascii=False, indent=2))


def openclaw_agent_markdown(name: str, summary: str, soul_text: str, memory_text: str, allowed_skills: list[str], wiki_path: Path) -> str:
    return f"""\
# {name} OPC Agent Spec

Target runtime: OpenClaw-compatible configuration package.

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
        sorted(set(spec["allowed_skills"])),
        wiki_path,
    )


def openclaw_agent_records(custom_specs: list[dict[str, Any]], wiki_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for profile in PROFILES:
        records.append({
            "name": profile,
            "kind": "core-agent",
            "role_summary": CORE_PROFILE_SUMMARY[profile],
            "prompt_file": f"agents/{profile}.md",
            "allowed_skills": sorted(ALLOWED_SKILLS[profile]),
            "wiki_path": str(wiki_path),
            "subagent_report_target": profile,
        })
    for spec in custom_specs:
        records.append({
            "name": spec["name"],
            "kind": "custom-peer-agent",
            "mission": spec["mission"],
            "prompt_file": f"agents/{spec['name']}.md",
            "allowed_skills": sorted(set(spec["allowed_skills"])),
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


def openclaw_import_doc(package: Path, wiki_path: Path) -> str:
    return f"""\
# OPC Team OpenClaw Package

This directory is a non-invasive OpenClaw-compatible configuration package. It does not edit `.openclaw/openclaw.json` because this local machine exposes Hermes OpenClaw migration helpers but no stable OpenClaw profile CLI.

## Files
- `manifest.json`: package metadata.
- `agents.json`: structured agent registry.
- `agents/*.md`: prompt and role-memory seeds for each core or custom Agent.
- `routing-table.md`: coordinator routing table.
- `discord-channel-routing.json`: one-token, multi-channel routing policy.
- `subagent-reporting.md`: temporary Subagent report contract.
- `wiki-template/`: seed Wiki pages for the shared memory model.

## Integration Pattern
1. Keep the shared Wiki at `{wiki_path}`.
2. Use `agents/*.md` as the source prompt/spec for OpenClaw agent definitions.
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
    (package / "wiki-template").mkdir(parents=True, exist_ok=True)

    records = openclaw_agent_records(custom_specs, args.wiki_path)
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
    write_generated_json(package / "agents.json", records)
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
                sorted(ALLOWED_SKILLS[profile]),
                args.wiki_path,
            ),
        )
    for spec in custom_specs:
        write_generated(package / "agents" / f"{spec['name']}.md", openclaw_custom_agent_markdown(spec, args.wiki_path))

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
        print("dry-run: would install/start coordinator gateway")
        return
    env = command_env(args.hermes_home)
    run(["coordinator", "gateway", "install"], env=env, check=False)
    run(["coordinator", "gateway", "start"], env=env, check=False)


def run_checks(args: argparse.Namespace, custom_specs: list[dict[str, Any]]) -> None:
    if args.dry_run:
        return
    env = command_env(args.hermes_home)
    run(["hermes", "profile", "list"], env=env, check=False)
    run(["coordinator", "gateway", "status"], env=env, check=False)
    if args.run_chat_checks:
        for profile in list(PROFILES) + [spec["name"] for spec in custom_specs]:
            run([profile, "chat", "-Q", "-q", "用一句话说明你的职责边界。"], env=env, check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=["hermes", "openclaw"], default="hermes", help="runtime/configuration target")
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--openclaw-home", type=Path, default=Path.home() / ".openclaw")
    parser.add_argument("--wiki-path", type=Path, help="absolute shared Wiki path; overrides vault selection")
    parser.add_argument("--vault-path", type=Path, help="shared vault root used with --wiki-folder-name")
    parser.add_argument("--wiki-folder-name", default=DEFAULT_WIKI_FOLDER_NAME, help="relative folder inside the selected vault; default '.' means the vault root")
    parser.add_argument("--select-vault", action="store_true", help="interactively choose the shared vault before initializing")
    parser.add_argument("--discord-channel-id")
    parser.add_argument("--discord-user-id")
    parser.add_argument("--discord-bot-token")
    parser.add_argument("--custom-profile-spec", action="append", help="JSON file containing one custom agent spec or a list of specs")
    parser.add_argument("--custom-profile-json", action="append", help="Inline JSON object for one custom peer agent")
    parser.add_argument("--custom-profile-preset", action="append", help="Built-in custom agent preset: growth-agent or secretary")
    parser.add_argument("--no-copy-auth", action="store_true", help="do not seed missing Hermes profile auth.json from the default Hermes home")
    parser.add_argument("--force-wiki", action="store_true", help="overwrite seed Wiki files")
    parser.add_argument("--start-gateway", action="store_true", help="install and start coordinator gateway after real Discord values are supplied")
    parser.add_argument("--run-chat-checks", action="store_true", help="spend model calls to check each role responds with its boundary")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.hermes_home = args.hermes_home.expanduser()
    args.openclaw_home = args.openclaw_home.expanduser()
    args.wiki_path = resolve_wiki_path(args)
    requested_custom_specs = load_custom_specs(args)

    if args.target == "hermes":
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
