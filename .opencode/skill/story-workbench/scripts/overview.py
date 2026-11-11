#!/usr/bin/env python3
"""Story Lab 项目总览生成器（只读汇总，不改事实源）。

用法:
    overview.py <slug> [--write]

- 读取 projects/<slug>/ 下的 project.yaml、bible/、structure/、episodes/、
  decisions.jsonl，生成一份给人看的项目总览。
- --write  写入 projects/<slug>/PROJECT.md。
- 不写参数时只打印到终端。

设计原则:
- PROJECT.md 是快照，不是事实源；任何结论都能从文件重新算出。
- 面向“不开 agent 也能看懂”：项目目标、计划、当前进度、质量风险、文件导航。
- 每次阶段完成或单集评审完成，由 SKILL.md 流程与 status.py --write 自动刷新。

退出码: 0 = 生成完成；1 = 用法/项目错误。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import status as st

ROOT = Path(__file__).resolve().parents[4]


def recent_decisions(proj: Path, limit: int = 5) -> list[dict]:
    path = proj / "decisions.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in st.read_text(path).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]


def protagonist_state(data: dict, latest_done: dict | None) -> dict:
    if not latest_done:
        return {}
    state = latest_done.get("state") if isinstance(latest_done.get("state"), dict) else {}
    chars = state.get("characters") or {}
    protagonist = next(
        (c for c in data["chars"] if c.get("role") == "protagonist"),
        None,
    )
    pid = str(protagonist.get("id")) if protagonist else ""
    return chars.get(pid) or {}


def render(data: dict) -> str:
    cfg = data["cfg"]
    title = str(cfg.get("title") or "未命名项目")
    n = data["n_eps"]
    target = data["target"]
    eps = data["episodes"]
    approved = [e for e in eps if e["status"] == "通过"]
    in_making = [e for e in eps if e["status"] in ("卡片", "待评", "待修", "异常")]
    current = next((e for e in eps if e["status"] != "通过"), None)
    latest_done = approved[-1] if approved else None
    logline = st.extract_logline(data["premise"])
    health = st.health_checks(data)
    pct = (len(approved) / n * 100) if n else 0
    next_action = st.next_step(data, current) if current else "全季已完成，进入导出/复盘"

    lines: list[str] = []
    lines.append(f"# 《{title}》项目总览")
    lines.append("")
    lines.append(
        f"> 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ "
        f"项目：`{st.rel(data['proj'])}` ｜ 本文件自动生成，勿手改"
    )
    lines.append(
        "> 事实源：`project.yaml` / `bible/` / `structure/` / `episodes/`；"
        "本文件与 `STATUS.md`、`CONTINUITY.md` 都是快照。"
    )
    lines.append("")

    # -------- 项目目标
    lines.append("## 项目目标")
    lines.append("")
    if logline:
        lines.append(f"**一句话**：{logline}")
        lines.append("")
    rows = [
        ["题材 / 平台", f"{cfg.get('genre', '—')} / {cfg.get('platform', '—')}"],
        ["规模", f"{n} 集 × {target} 秒"],
        ["受众", cfg.get("audience", "—")],
        ["禁忌", "、".join(map(str, cfg.get("taboos") or [])) or "—"],
        ["总目标", f"完成全部 {n} 集，并通过场景卡/剧本/评审三道闸门"],
    ]
    lines.append(st.md_table(["项", "内容"], rows))
    lines.append("")

    # -------- 计划执行
    lines.append("## 计划执行")
    lines.append("")
    if data["movements"]:
        rows = []
        for m in data["movements"]:
            rng = st.movement_range(m)
            start, end = rng if rng else (0, 0)
            done = sum(1 for e in approved if start <= e["ep"] <= end)
            total = max(end - start + 1, 0)
            rows.append([
                f"{m.get('id', '?')} · {m.get('name', '')}",
                f"e{start:02d}–e{end:02d}",
                st.truncate(m.get("goal", ""), 46),
                f"{done}/{total}",
                f"`{st.bar(done, total)}`",
            ])
        lines.append(st.md_table(["乐章", "集数", "阶段目标", "已通过", "进度"], rows))
    else:
        lines.append("_movements.yaml 缺失，暂无乐章计划。_")
    lines.append("")

    if data["pinned_eps"]:
        pins = []
        for ep in sorted(data["pinned_eps"]):
            p = data["pinned_eps"][ep]
            pins.append(f"e{ep:02d} {p.get('kind', '钉死集')}（{p.get('note', '')}）")
        lines.append(f"**钉死集**：{'；'.join(pins)}")
        lines.append("")

    if current:
        lines.append("### 接下来 3 集")
        lines.append("")
        rows = []
        for ep in range(current["ep"], min(n, current["ep"] + 2) + 1):
            e = eps[ep - 1]
            h = data["hooks_by_ep"].get(ep, {})
            rows.append([
                f"e{ep:02d}",
                st.STATUS_TEXT.get(e["status"], e["status"]),
                st.truncate(h.get("question_left_open", "—"), 30),
                h.get("cliffhanger_type", "—"),
                f"{h.get('value_before', '—')}→{h.get('value_after', '—')}",
            ])
        lines.append(st.md_table(["集", "状态", "集末问题", "悬念类型", "价值线"], rows))
        lines.append("")

    # -------- 当前进度
    lines.append("## 当前进度")
    lines.append("")
    rows = [
        ["已通过", f"{len(approved)} / {n} 集（{pct:.1f}%）"],
        ["在制", f"{len(in_making)} 集"],
        ["当前集", f"e{current['ep']:02d}（{st.STATUS_TEXT.get(current['status'], current['status'])}）" if current else "全季完成"],
        ["下一步", next_action],
        ["决策日志", f"{data['decisions']} 条"],
    ]
    lines.append(st.md_table(["项", "状态"], rows))
    lines.append("")

    if approved:
        lines.append("### 最近完成")
        lines.append("")
        rows = []
        for e in approved[-5:]:
            r = e["review"] or {}
            score = f"{e['review_total']}/{e['review_threshold']}"
            flag = " · force_pass" if r.get("force_pass") else ""
            reviewer = "自评" if "self" in str(e["reviewer"]).lower() else "独立"
            rows.append([
                f"e{e['ep']:02d}",
                score,
                st.STATUS_TEXT.get(e["status"], e["status"]) + flag,
                f"round {e['review_round']} · {reviewer}",
            ])
        lines.append(st.md_table(["集", "评审", "结论", "轮次"], rows))
        lines.append("")

    if latest_done:
        h = data["hooks_by_ep"].get(latest_done["ep"], {})
        ps = protagonist_state(data, latest_done)
        lines.append("### 故事现在到哪")
        lines.append("")
        lines.append(f"- 上一集末价值：**{h.get('value_after', '—')}**")
        lines.append(f"- 上一集留下的问题：{h.get('question_left_open', '—')}")
        if ps.get("knows"):
            lines.append(f"- 主角已知：{'；'.join(map(str, ps['knows'][:4]))}")
        if ps.get("believes"):
            lines.append(f"- 主角判断：{'；'.join(map(str, ps['believes'][:3]))}")
        if ps.get("suspects"):
            lines.append(f"- 主角起疑：{'；'.join(map(str, ps['suspects'][:3]))}")
        state = latest_done["state"] if isinstance(latest_done["state"], dict) else {}
        open_threads = state.get("open_threads") or []
        lines.append(f"- 未回收伏笔：{', '.join(map(str, open_threads)) or '无'}")
        lines.append("")

    # -------- 质量与风险
    lines.append("## 质量与风险")
    lines.append("")
    force_pass = [e for e in approved if (e["review"] or {}).get("force_pass")]
    warnings = sum(len(e["warnings"]) for e in eps if e["review"])
    blockers = sum(len(e["blockers"]) for e in eps if e["review"])
    rows = [
        ["未解决 blocker", f"{blockers} 条"],
        ["累计 warning", f"{warnings} 条"],
        ["force_pass", f"{len(force_pass)} 集" + (
            "（" + "、".join(f"e{e['ep']:02d}" for e in force_pass) + "）" if force_pass else "")],
    ]
    lines.append(st.md_table(["项", "数量"], rows))
    lines.append("")
    if health:
        lines.append("**需要人工确认**：")
        lines.append("")
        for item in health:
            lines.append(f"- {item}")
    else:
        lines.append("**需要人工确认**：暂无。")
    lines.append("")

    # -------- 文件导航
    lines.append("## 文件导航")
    lines.append("")
    rows = [
        ["`project.yaml`", "项目配置：题材、集数、时长、受众、禁忌"],
        ["`bible/premise.md`", "立意、logline、故事引擎"],
        ["`bible/characters/`", "人物卡：want/fear/secret/voice"],
        ["`bible/relations.yaml`", "人物关系与翻脸点"],
        ["`structure/movements.yaml`", "五乐章与钉死集"],
        ["`structure/hooks.yaml`", "全季钩子、价值线、悬念类型"],
        ["`structure/threads.yaml`", "伏笔账本"],
        ["`episodes/eNN/`", "每集四件套：cards / script / state / review"],
        ["`STATUS.md`", "状态看板快照"],
        ["`CONTINUITY.md`", "跨集连续性巡检快照"],
        ["`decisions.jsonl`", "选择、修改、否决、force_pass 的留痕"],
    ]
    lines.append(st.md_table(["文件", "内容"], rows))
    lines.append("")

    decisions = recent_decisions(data["proj"])
    if decisions:
        lines.append("## 最近决策")
        lines.append("")
        for d in decisions:
            ts = str(d.get("ts", ""))[:10]
            stage = d.get("stage", "?")
            action = d.get("action", "?")
            chosen = st.truncate(d.get("chosen", ""), 56)
            reason = st.truncate(d.get("reason", ""), 60)
            lines.append(f"- `{ts}` **{stage} / {action}**：{chosen}" + (f"（{reason}）" if reason else ""))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "本文件由 `scripts/overview.py` 生成；每次阶段完成或单集评审完成会自动刷新。"
        "手动刷新：`python scripts/overview.py <slug> --write`。"
    )
    lines.append("")
    return "\n".join(lines)


def write_overview(proj: Path, data: dict | None = None) -> Path:
    data = data or st.build_dataset(proj)
    text = render(data)
    out = proj / "PROJECT.md"
    out.write_text(text + "\n", encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Story Lab 项目总览生成器（只读汇总）")
    ap.add_argument("slug", help="projects/<slug>")
    ap.add_argument("--write", action="store_true", help="写入 projects/<slug>/PROJECT.md")
    args = ap.parse_args()

    proj = ROOT / "projects" / args.slug
    if not proj.is_dir():
        print(f"项目不存在: {proj}", file=sys.stderr)
        return 1

    data = st.build_dataset(proj)
    text = render(data)
    print(text)
    if args.write:
        out = write_overview(proj, data)
        print()
        print(f"已写入 {st.rel(out)}（项目总览）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
