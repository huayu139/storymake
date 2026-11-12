#!/usr/bin/env python3
"""Story Lab 状态看板生成器（只读汇总，不改事实源）。

用法:
    status.py <slug> [--write] [--full]

- 读取 projects/<slug>/ 下的 project.yaml、bible/、structure/、episodes/、
  decisions.jsonl，汇总成中文 Markdown 状态看板。
- --write  额外写入 projects/<slug>/STATUS.md（完整 70 集版）与
           projects/<slug>/PROJECT.md（项目总览），终端仍打印看板。
- --full   终端也输出完整逐集表（默认只给紧凑进度网格 + 当前窗口）。

设计原则:
- 只读：不修改 bible/structure/episodes 等事实源；STATUS.md 只是快照。
- 可重复：任何结论都能从文件重新算出，不依赖人工记忆。
- 先说人话：开头给总览与“故事进行到哪”，细节表放后面。

退出码: 0 = 汇总完成（数据问题以“数据健康”列出，不阻断）；1 = 用法/项目错误。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

# 本脚本位于 .opencode/skill/story-workbench/scripts/status.py
ROOT = Path(__file__).resolve().parents[4]

ROLE_CN = {
    "protagonist": "主角",
    "antagonist": "反派",
    "supporting": "配角",
}
STATUS_SYMBOL = {
    "通过": "✔",
    "卡片": "◐",
    "待评": "◐",
    "待修": "✖",
    "未写": "·",
    "异常": "!",
}
STATUS_TEXT = {
    "通过": "已通过",
    "卡片": "场景卡完成",
    "待评": "待评审",
    "待修": "待修复",
    "未写": "未开始",
    "异常": "产物异常",
}


# ---------------------------------------------------------------- 基础工具
def read_yaml(path: Path, errors: list[str]):
    """读 YAML；失败返回 None 并记一条数据问题。"""
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel(path)} 解析失败：{e}")
        return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def cjk_len(text: str) -> int:
    """与 validate.py 一致：中文按字、英文按词。"""
    return len(re.findall(r"[一-鿿]", text)) + len(re.findall(r"[A-Za-z]+", text))


_DIRECTIVE_RE = re.compile(
    r"^【场景】.*?(?=^【节拍|^## |\Z)"   # 【场景】块（标签行 + 描述段）
    r"|^【人物】[^\n]*\n?",               # 【人物】行
    flags=re.S | re.M,
)


def performance_text(text: str) -> str:
    """与 validate.py 一致：扣除【场景】【人物】说明块，只留表演正文计时。"""
    return _DIRECTIVE_RE.sub("", text or "")


def as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truncate(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def md_cell(value) -> str:
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(md_cell(v) for v in row) + " |")
    return "\n".join(out)


def bar(done: int, total: int, width: int = 12) -> str:
    if total <= 0:
        return "░" * width
    filled = round(width * min(done, total) / total)
    return "█" * filled + "░" * (width - filled)


def extract_logline(premise: str) -> str:
    m = re.search(r"##\s*Logline\s*\n+(.+?)(?:\n\s*\n|\n##|\Z)", premise, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()


def movement_range(m: dict) -> tuple[int, int] | None:
    rng = m.get("episodes") or []
    if not isinstance(rng, list) or not rng:
        return None
    start = as_int(rng[0])
    end = as_int(rng[1]) if len(rng) > 1 else start
    return (min(start, end), max(start, end))


# ---------------------------------------------------------------- 数据汇总
def episode_info(proj: Path, ep: int, target_seconds: int, errors: list[str]) -> dict:
    d = proj / f"episodes/e{ep:02d}"
    cards = read_yaml(d / "cards.yaml", errors)
    script = read_text(d / "script.md")
    state = read_yaml(d / "state.yaml", errors)
    review = read_yaml(d / "review.yaml", errors)

    notes: list[str] = []
    if cards is not None and not isinstance(cards, list):
        notes.append("cards.yaml 不是数组")
        cards_list = []
    else:
        cards_list = cards or []
    if script and not state:
        notes.append("缺 state.yaml")
    if review and not script:
        notes.append("有 review 但缺 script")

    if review:
        verdict = review.get("verdict")
        if verdict == "approved":
            status = "通过"
        elif verdict == "needs_revision":
            status = "待修"
        else:
            status = "异常"
            notes.append("review.verdict 非法")
    elif script:
        status = "待评"
    elif cards is not None:
        status = "卡片"
    else:
        status = "未写"

    if status == "通过" and notes:
        status = "异常"

    total = review.get("total") if isinstance(review, dict) else None
    if total is None and isinstance(review, dict) and isinstance(review.get("scores"), dict):
        total = sum(as_int(v.get("score")) for v in review["scores"].values() if isinstance(v, dict))
    issues = (review or {}).get("issues") or [] if isinstance(review, dict) else []
    warnings = [
        i for i in issues
        if isinstance(i, dict)
        and i.get("severity") == "warning"
        and not i.get("resolved_after_review")
    ]
    blockers = [
        i for i in issues
        if isinstance(i, dict)
        and i.get("severity") == "blocker"
        and not i.get("resolved_after_review")
    ]

    card_seconds = sum(as_int(c.get("estimated_seconds")) for c in cards_list if isinstance(c, dict))
    return {
        "ep": ep,
        "status": status,
        "notes": notes,
        "cards": cards_list,
        "scenes": len(cards_list),
        "card_seconds": card_seconds,
        "script": bool(script),
        "script_chars": cjk_len(performance_text(script)),
        "script_seconds": cjk_len(performance_text(script)) / 4.5 if script else 0.0,
        "state": state,
        "review": review if isinstance(review, dict) else None,
        "review_total": total,
        "review_threshold": (review or {}).get("threshold", 32) if isinstance(review, dict) else None,
        "review_round": (review or {}).get("round") if isinstance(review, dict) else None,
        "review_verdict": (review or {}).get("verdict") if isinstance(review, dict) else None,
        "reviewer": (review or {}).get("reviewer", "") if isinstance(review, dict) else "",
        "warnings": warnings,
        "blockers": blockers,
        "duration_over": bool(script) and target_seconds > 0
                         and (cjk_len(performance_text(script)) / 4.5) > target_seconds * 1.2,
    }


def build_dataset(proj: Path) -> dict:
    errors: list[str] = []
    cfg = read_yaml(proj / "project.yaml", errors) or {}
    premise = read_text(proj / "bible/premise.md")
    voice = read_text(proj / "bible/voice.md")
    world = read_text(proj / "bible/world.md")

    chars = []
    for f in sorted((proj / "bible/characters").glob("*.yaml")):
        c = read_yaml(f, errors)
        if isinstance(c, dict):
            c["_file"] = f.name
            chars.append(c)
    relations = read_yaml(proj / "bible/relations.yaml", errors) or []

    movements_doc = read_yaml(proj / "structure/movements.yaml", errors) or {}
    movements = movements_doc.get("movements") if isinstance(movements_doc, dict) else []
    movements = movements or []
    pinned_eps = {
        as_int(p.get("episode")): p
        for p in (movements_doc.get("pinned_episodes") or [])
        if isinstance(p, dict)
    }
    hooks = read_yaml(proj / "structure/hooks.yaml", errors) or []
    hooks = [h for h in hooks if isinstance(h, dict)] if isinstance(hooks, list) else []
    hooks_by_ep = {as_int(h.get("episode")): h for h in hooks}
    threads = read_yaml(proj / "structure/threads.yaml", errors) or []
    threads = [t for t in threads if isinstance(t, dict)] if isinstance(threads, list) else []

    n_eps = as_int(cfg.get("episodes"), 1)
    target = as_int(cfg.get("seconds_per_episode"), 90)
    episodes = [episode_info(proj, ep, target, errors) for ep in range(1, n_eps + 1)]

    decisions = 0
    dpath = proj / "decisions.jsonl"
    if dpath.exists():
        decisions = sum(1 for line in read_text(dpath).splitlines() if line.strip())
    else:
        errors.append("decisions.jsonl 不存在")

    return {
        "proj": proj,
        "cfg": cfg,
        "premise": premise,
        "voice": bool(voice),
        "world": bool(world),
        "chars": chars,
        "relations": relations if isinstance(relations, list) else [],
        "movements": movements,
        "pinned_eps": pinned_eps,
        "hooks": hooks,
        "hooks_by_ep": hooks_by_ep,
        "threads": threads,
        "episodes": episodes,
        "n_eps": n_eps,
        "target": target,
        "decisions": decisions,
        "errors": errors,
    }


# ---------------------------------------------------------------- 派生判断
def thread_rows(data: dict) -> list[dict]:
    written = {e["ep"] for e in data["episodes"] if e["script"]}
    latest_written = max(written, default=0)
    rows = []
    for t in data["threads"]:
        plant = as_int(t.get("planted_at"))
        payoff = as_int(t.get("planned_payoff"))
        explicit = str(t.get("status") or "")
        if explicit == "paid":
            state = "已回收（账本标注）"
        elif explicit == "dropped":
            state = "已放弃（账本标注）"
        elif explicit in ("building",) and plant in written:
            state = "推进中"
        elif plant in written:
            if payoff in written:
                state = "已回收（按计划）"
            elif latest_written > payoff:
                state = "逾期未收"
            else:
                state = "已埋设"
        else:
            state = f"待埋设（计划 e{plant:02d}）"
        rows.append({
            "id": t.get("id", "?"),
            "desc": t.get("description", ""),
            "plant": plant,
            "payoff": payoff,
            "state": state,
            "raw_status": explicit,
            "note": t.get("note", ""),
        })
    return rows


def health_checks(data: dict) -> list[str]:
    issues: list[str] = []
    title = str(data["cfg"].get("title", ""))
    if "待定" in title or not title:
        issues.append("project.yaml 标题仍为空或“待定”，请回填正式剧名。")

    written = {e["ep"] for e in data["episodes"] if e["script"]}
    latest_written = max(written, default=0)

    stale = [t for t in data["threads"]
             if str(t.get("status")) == "planted" and as_int(t.get("planted_at")) > latest_written]
    if stale:
        issues.append(
            f"{len(stale)} 条伏笔标着 status=planted，但 planted_at 晚于最新已写集 "
            f"e{latest_written:02d}；看板已按 planted_at 重新推算，账本状态字段暂不可信。")

    for e in data["episodes"]:
        r = e["review"]
        if not r:
            continue
        scores = r.get("scores") if isinstance(r.get("scores"), dict) else {}
        if scores:
            calc = sum(as_int(v.get("score")) for v in scores.values() if isinstance(v, dict))
            if r.get("total") is not None and as_int(r.get("total")) != calc:
                issues.append(f"e{e['ep']:02d} review.total={r.get('total')} 与 8 维合计 {calc} 不一致。")
        if r.get("verdict") == "approved" and e["blockers"]:
            issues.append(f"e{e['ep']:02d} 标记 approved，但 issues 里仍有 blocker。")
        if "self" in str(e["reviewer"]).lower():
            issues.append(f"e{e['ep']:02d} 的评审是自评（reviewer={e['reviewer']}），建议额度恢复后补独立复评。")
        if e["duration_over"]:
            issues.append(
                f"e{e['ep']:02d} 剧本约 {e['script_seconds']:.1f}s，超过目标 "
                f"{data['target']}s 的 +20% 上限。")
        if e["card_seconds"] and e["script_seconds"] and \
                abs(e["script_seconds"] - e["card_seconds"]) / max(e["card_seconds"], 1) > 0.2:
            issues.append(
                f"e{e['ep']:02d} 卡片预估 {e['card_seconds']}s，成稿 {e['script_seconds']:.1f}s，"
                f"偏差超过 20%。")
        if e["status"] == "通过" and not e["state"]:
            issues.append(f"e{e['ep']:02d} 已通过但缺 state.yaml。")
        if e["status"] in ("卡片", "待评", "待修") and e["notes"]:
            issues.append(f"e{e['ep']:02d} 产物注记：{'；'.join(e['notes'])}。")

    if data["hooks"] and len(data["hooks"]) != data["n_eps"]:
        issues.append(f"hooks.yaml 有 {len(data['hooks'])} 条，项目配置 {data['n_eps']} 集，数量不一致。")

    covered = set()
    for m in data["movements"]:
        rng = movement_range(m)
        if rng:
            covered |= set(range(rng[0], rng[1] + 1))
    if data["movements"]:
        missing = sorted(set(range(1, data["n_eps"] + 1)) - covered)
        if missing:
            issues.append(f"movements.yaml 未覆盖 {len(missing)} 集：e{missing[0]:02d}–e{missing[-1]:02d}。")

    for e in data["episodes"]:
        if e["status"] == "通过" and e["review"] and e["review_round"] and as_int(e["review_round"]) < 2:
            pass

    return issues


# ---------------------------------------------------------------- 渲染
def render(data: dict, full: bool) -> str:
    cfg = data["cfg"]
    title = str(cfg.get("title") or "未命名项目")
    n = data["n_eps"]
    eps = data["episodes"]
    approved = [e for e in eps if e["status"] == "通过"]
    in_making = [e for e in eps if e["status"] in ("卡片", "待评", "待修", "异常")]
    current = next((e for e in eps if e["status"] != "通过"), None)
    latest_done = approved[-1] if approved else None
    logline = extract_logline(data["premise"])
    threads = thread_rows(data)
    health = health_checks(data)
    lines: list[str] = []

    lines.append(f"# 《{title}》故事状态看板")
    lines.append("")
    lines.append(
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ "
        f"项目：`{rel(data['proj'])}` ｜ 状态文件只读汇总，事实源仍是 bible/structure/episodes")
    lines.append("")

    # -------- 总览
    lines.append("## 总览")
    lines.append("")
    pct = (len(approved) / n * 100) if n else 0
    if current:
        next_action = next_step(data, current)
        current_text = f"e{current['ep']:02d}（{STATUS_TEXT.get(current['status'], current['status'])}）"
    else:
        next_action = "全季已完成，进入导出/复盘"
        current_text = "全季完成"
    rows = [
        ["题材 / 平台", f"{cfg.get('genre', '—')} / {cfg.get('platform', '—')}"],
        ["规模", f"{n} 集 × {data['target']} 秒"],
        ["当前进度", f"{len(approved)} / {n} 集已通过（{pct:.1f}%）"],
        ["在制 / 未开始", f"{len(in_making)} 集 / {n - len(approved) - len(in_making)} 集"],
        ["当前集", current_text],
        ["下一步", next_action],
        ["决策日志", f"{data['decisions']} 条"],
        ["故事引擎", "菜市场微型江湖：18 摊位 × 收购七连招 × 房东身份层层剥" if data["world"] else "—"],
    ]
    lines.append(md_table(["项", "值"], rows))
    lines.append("")
    if logline:
        lines.append(f"> **Logline**：{logline}")
        lines.append("")

    # -------- 故事进行到哪
    lines.append("## 故事进行到哪")
    lines.append("")
    if latest_done:
        h = data["hooks_by_ep"].get(latest_done["ep"], {})
        if h:
            lines.append(f"- 上集（e{latest_done['ep']:02d}）末价值：**{h.get('value_after', '—')}**")
            lines.append(f"- 上集留下的问题：{h.get('question_left_open', '—')}")
        state = latest_done["state"] if isinstance(latest_done["state"], dict) else {}
        state_chars = state.get("characters") or {}
        zn = state_chars.get("zhou-liping") or {}
        if zn:
            knows = [str(x) for x in (zn.get("knows") or [])]
            believes = [str(x) for x in (zn.get("believes") or [])]
            suspects = [str(x) for x in (zn.get("suspects") or [])]
            if knows:
                lines.append(f"- 主角已知道：{'；'.join(knows[:4])}")
            if believes:
                lines.append(f"- 主角当前判断：{'；'.join(believes[:3])}")
            if suspects:
                lines.append(f"- 主角起疑：{'；'.join(suspects[:3])}")
        open_t = state.get("open_threads") or []
        if open_t:
            lines.append(f"- 未回收伏笔：{', '.join(map(str, open_t))}")
        else:
            lines.append("- 未回收伏笔：无（当前仅软前置，正式埋设见伏笔账本）")
    else:
        lines.append("- 还没有通过评审的集，故事尚未正式展开。")
    if current:
        h = data["hooks_by_ep"].get(current["ep"], {})
        if h:
            lines.append(
                f"- 下一集（e{current['ep']:02d}）钩子：{h.get('question_left_open', '—')}"
                f"（{h.get('cliffhanger_type', '—')}，"
                f"{h.get('value_before', '—')}→{h.get('value_after', '—')}）")
    lines.append("")

    # -------- 五乐章
    lines.append("## 五乐章进度")
    lines.append("")
    if data["movements"]:
        rows = []
        for m in data["movements"]:
            rng = movement_range(m)
            start, end = rng if rng else (0, 0)
            done = sum(1 for e in approved if start <= e["ep"] <= end)
            total = max(end - start + 1, 0)
            rows.append([
                f"{m.get('id', '?')} · {m.get('name', '')}",
                f"e{start:02d}–e{end:02d}",
                f"{done}/{total}",
                f"`{bar(done, total)}`",
            ])
        lines.append(md_table(["乐章", "集数", "已通过", "进度"], rows))
    else:
        lines.append("_movements.yaml 缺失_")
    lines.append("")

    # -------- 逐集进度
    lines.append("## 逐集进度")
    lines.append("")
    lines.append("符号：`✔` 已通过 ｜ `◐` 制作中 ｜ `✖` 待修复 ｜ `·` 未开始 ｜ `!` 产物异常")
    lines.append("")
    tokens = [f"e{e['ep']:02d}{STATUS_SYMBOL.get(e['status'], '?')}" for e in eps]
    for i in range(0, len(tokens), 10):
        lines.append("  ".join(tokens[i:i + 10]))
    lines.append("")
    if full:
        rows = []
        for e in eps:
            h = data["hooks_by_ep"].get(e["ep"], {})
            value = f"{h.get('value_before', '—')}→{h.get('value_after', '—')}" if h else "—"
            ct = str(h.get("cliffhanger_type", "—"))
            pinned = h.get("pinned") or e["ep"] in data["pinned_eps"]
            if pinned:
                ct = f"★{ct}"
            q = truncate(h.get("question_left_open", ""), 28) if h else "—"
            sec = f"{e['script_seconds']:.1f}" if e["script"] else "—"
            if e["review"]:
                review = f"{e['review_total']}/{e['review_threshold']} {STATUS_TEXT.get(e['status'], e['status'])}"
            else:
                review = "—"
            rows.append([f"e{e['ep']:02d}", STATUS_TEXT.get(e["status"], e["status"]), value, ct, q, sec, review])
        lines.append(md_table(["集", "状态", "价值线", "悬念", "钩子问题", "剧本秒", "评审"], rows))
    else:
        window = range(1, n + 1)
        if current:
            window = range(max(1, current["ep"] - 2), min(n, current["ep"] + 2) + 1)
        rows = []
        for i in window:
            e = eps[i - 1]
            h = data["hooks_by_ep"].get(e["ep"], {})
            rows.append([
                f"e{e['ep']:02d}",
                STATUS_TEXT.get(e["status"], e["status"]),
                f"{h.get('value_before', '—')}→{h.get('value_after', '—')}" if h else "—",
                h.get("cliffhanger_type", "—"),
                truncate(h.get("question_left_open", ""), 26) if h else "—",
            ])
        lines.append(md_table(["集", "状态", "价值线", "悬念", "钩子问题"], rows))
        if n > len(list(window)):
            lines.append("")
            lines.append("_终端为紧凑视图；完整逐集表用 `--full`，或 `--write` 生成 STATUS.md。_")
    lines.append("")

    # -------- 伏笔
    lines.append("## 伏笔账本")
    lines.append("")
    if threads:
        rows = []
        for t in threads:
            rows.append([
                t["id"],
                truncate(t["desc"], 34),
                f"e{t['plant']:02d}",
                f"e{t['payoff']:02d}",
                t["state"],
            ])
        lines.append(md_table(["ID", "伏笔", "埋设", "回收", "当前状态"], rows))
        lines.append("")
        lines.append("_状态按 planted_at/planned_payoff 与已写剧本集数推算，不替代人工确认。_")
    else:
        lines.append("_threads.yaml 缺失_")
    lines.append("")

    # -------- 人物
    lines.append("## 人物状态")
    lines.append("")
    latest_state = latest_done["state"] if latest_done and isinstance(latest_done["state"], dict) else {}
    state_chars = latest_state.get("characters") or {}
    order = {"protagonist": 0, "antagonist": 1, "supporting": 2}
    chars_sorted = sorted(data["chars"], key=lambda c: (order.get(c.get("role"), 9), str(c.get("name", ""))))
    rows = []
    for c in chars_sorted:
        cid = str(c.get("id", ""))
        st = state_chars.get(cid) or {}
        loc = st.get("location", "—")
        knows = len(st.get("knows") or [])
        changes = "；".join(str(x) for x in (st.get("relationship_changes") or [])) or "—"
        flag = "已退场" if st.get("written_out") else ("死亡" if st.get("dead") else "在场")
        if not st:
            loc, knows, changes, flag = "—", "—", "—", "未出场"
        rows.append([
            f"{c.get('name', cid)} · {ROLE_CN.get(c.get('role'), c.get('role', '—'))}",
            truncate(loc, 14),
            f"{knows} 条" if st else "—",
            truncate(changes, 26),
            flag,
        ])
    lines.append(md_table(["角色", "当前地点", "已知", "关系变化", "状态"], rows))
    lines.append("")

    # -------- 质量
    lines.append("## 质量与评审")
    lines.append("")
    done_rows = []
    for e in eps:
        if not (e["script"] or e["review"] or e["cards"]):
            continue
        review = "—"
        if e["review"]:
            reviewer = "自评" if "self" in str(e["reviewer"]).lower() else "独立"
            review = (f"{e['review_total']}/{e['review_threshold']} "
                      f"{STATUS_TEXT.get(e['status'], e['status'])} · "
                      f"round {e['review_round']} · {reviewer}")
        dur = f"{e['script_seconds']:.1f}s" if e["script"] else "—"
        warn_n = len(e["warnings"])
        done_rows.append([f"e{e['ep']:02d}", STATUS_TEXT.get(e["status"], e["status"]), dur, review,
                          f"{warn_n} 条" if e["review"] else "—"])
    if done_rows:
        lines.append(md_table(["集", "状态", "剧本时长", "评审", "warning"], done_rows))
    else:
        lines.append("_暂无已制作集_")
    lines.append("")

    # -------- 数据健康
    lines.append("## 数据健康")
    lines.append("")
    if health:
        for item in health:
            lines.append(f"- {item}")
    else:
        lines.append("- 未发现明显数据矛盾。")
    if data["errors"]:
        for item in data["errors"]:
            lines.append(f"- 读取问题：{item}")
    lines.append("")

    # -------- 下一步
    lines.append("## 下一步")
    lines.append("")
    step = 1
    lines.append(f"{step}. **{next_action}**")
    step += 1
    if latest_done and latest_done["warnings"]:
        codes = "、".join(sorted({str(i.get("code", "?")) for i in latest_done["warnings"]}))
        lines.append(f"{step}. e{latest_done['ep']:02d} 还有 {len(latest_done['warnings'])} 条非阻断 warning 可打磨：{codes}")
        step += 1
    if latest_done and latest_done["review"]:
        polish = latest_done["review"].get("optional_polish") or []
        if polish:
            lines.append(f"{step}. e{latest_done['ep']:02d} 有 {len(polish)} 条可选打磨项（见 review.yaml.optional_polish）")
            step += 1
    lines.append(f"{step}. 修改 skill 后回归：`evals/run_evals.py`")
    lines.append("")
    return "\n".join(lines)


def next_step(data: dict, current: dict) -> str:
    ep = current["ep"]
    status = current["status"]
    if status == "未写":
        return f"S5 场景卡：写 e{ep:02d}/cards.yaml"
    if status == "卡片":
        return f"S6 剧本：写 e{ep:02d}/script.md + state.yaml"
    if status == "待评":
        return f"S7 评审：生成 e{ep:02d}/review.yaml"
    if status == "待修":
        return f"回 S6 修复 e{ep:02d}，然后复评"
    if status == "异常":
        return f"先检查 e{ep:02d} 的产物完整性"
    return "继续下一集"


# ---------------------------------------------------------------- 入口
def main() -> int:
    ap = argparse.ArgumentParser(description="Story Lab 状态看板生成器（只读）")
    ap.add_argument("slug", help="projects/<slug>")
    ap.add_argument("--write", action="store_true", help="写入 STATUS.md 与 PROJECT.md（完整版）")
    ap.add_argument("--full", action="store_true", help="终端输出完整逐集表")
    args = ap.parse_args()

    proj = ROOT / "projects" / args.slug
    if not proj.is_dir():
        print(f"项目不存在: {proj}", file=sys.stderr)
        return 1

    data = build_dataset(proj)
    text = render(data, full=args.full or args.write)
    print(text)

    if args.write:
        out = proj / "STATUS.md"
        out.write_text(text + "\n", encoding="utf-8")
        print()
        print(f"已写入 {rel(out)}（完整 70 集版）")
        try:
            import overview

            overview_out = overview.write_overview(proj, data)
            print(f"已写入 {rel(overview_out)}（项目总览）")
        except Exception as e:  # noqa: BLE001
            print(f"PROJECT.md 生成失败：{e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
