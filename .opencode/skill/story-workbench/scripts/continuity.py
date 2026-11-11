#!/usr/bin/env python3
"""Story Lab 连续性巡检与集末状态账本（只读）。

用法:
    continuity.py <slug> [--write]

检查（跨集）:
    K1 有剧本但缺 state.yaml
    K2 已死亡/退场人物在后续集 cards 中复出
    K3 相邻集价值链接不上（上集 value_after ≠ 下集 value_before）
    K4 伏笔提前挂账 / 未知伏笔 / 到期未收 / 埋设集未挂账
    K5 人物集间位置突变，剧本里找不到过渡依据
    K6 道具账本断链（上集存在、本集无处置地消失）
    K7 剧本时长超出目标 ±20%
    K8 剧本缺评审、总分不一致、approved 但仍有 blocker

--write 额外生成 projects/<slug>/CONTINUITY.md（集末状态账本 + 问题清单）。
退出码: 0 = 无 BLOCKER；1 = 有 BLOCKER 或用法错误。
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]

issues: list[dict] = []


def blocker(rule: str, msg: str, loc: str = "") -> None:
    issues.append({"level": "BLOCKER", "rule": rule, "msg": msg, "loc": loc})


def warn(rule: str, msg: str, loc: str = "") -> None:
    issues.append({"level": "WARN", "rule": rule, "msg": msg, "loc": loc})


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_yaml(path: Path):
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        blocker("K0", f"{rel(path)} 解析失败：{e}", str(path))
        return None


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def cjk_len(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text)) + len(re.findall(r"[A-Za-z]+", text))


def as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def loc_tokens(location: str) -> list[str]:
    """把“鱼摊（B7）”“市场通道 → 对面（离开）”拆成可匹配片段。"""
    if not location:
        return []
    text = re.sub(r"[（(][^）)]*[）)]", "", str(location))
    parts = re.split(r"[·/→\s]+", text)
    return [p for p in parts if len(p) >= 2]


def loc_in_text(location: str, text: str) -> bool:
    if not location:
        return True
    if str(location) in text:
        return True
    return any(tok in text for tok in loc_tokens(location))


def review_total(review: dict) -> int:
    scores = review.get("scores") if isinstance(review, dict) else {}
    if not isinstance(scores, dict):
        return 0
    return sum(as_int(v.get("score")) for v in scores.values() if isinstance(v, dict))


def collect(proj: Path) -> dict:
    cfg = load_yaml(proj / "project.yaml") or {}
    n = as_int(cfg.get("episodes"), 1)
    target = as_int(cfg.get("seconds_per_episode"), 90)
    hooks = load_yaml(proj / "structure/hooks.yaml") or []
    hooks = [h for h in hooks if isinstance(h, dict)]
    hooks_by_ep = {as_int(h.get("episode")): h for h in hooks}
    threads = load_yaml(proj / "structure/threads.yaml") or []
    threads = [t for t in threads if isinstance(t, dict)]
    threads_by_id = {str(t.get("id")): t for t in threads}

    episodes = []
    for ep in range(1, n + 1):
        d = proj / f"episodes/e{ep:02d}"
        cards = load_yaml(d / "cards.yaml")
        script = load_text(d / "script.md")
        state = load_yaml(d / "state.yaml")
        review = load_yaml(d / "review.yaml")
        if not (isinstance(cards, list) and cards) and not script:
            continue
        episodes.append({
            "ep": ep,
            "cards": cards if isinstance(cards, list) else [],
            "script": script,
            "state": state if isinstance(state, dict) else None,
            "review": review if isinstance(review, dict) else None,
        })
    return {
        "proj": proj, "cfg": cfg, "n": n, "target": target,
        "hooks_by_ep": hooks_by_ep, "threads": threads, "threads_by_id": threads_by_id,
        "episodes": episodes,
        "latest": max((e["ep"] for e in episodes), default=0),
    }


def check_value_chain(data: dict) -> None:
    eps = sorted(data["hooks_by_ep"])
    for a, b in zip(eps, eps[1:]):
        if b != a + 1:
            continue
        after = data["hooks_by_ep"][a].get("value_after")
        before = data["hooks_by_ep"][b].get("value_before")
        if after and before and after != before:
            blocker("K3", f"e{a:02d} 末价值「{after}」≠ e{b:02d} 初价值「{before}」",
                    "structure/hooks.yaml")


def check_episodes(data: dict) -> None:
    prev_state: dict | None = None
    prev_ep = 0
    dead: set[str] = set()

    for e in data["episodes"]:
        ep, d = e["ep"], data["proj"] / f"episodes/e{e['ep']:02d}"
        script, state, cards, review = e["script"], e["state"], e["cards"], e["review"]

        if script and not state:
            blocker("K1", f"e{ep:02d} 有剧本但缺 state.yaml", rel(d / "state.yaml"))

        # K2 死亡/退场人物复出
        for c in cards:
            for cid in (c.get("cast") or []):
                if cid in dead:
                    blocker("K2", f"e{ep:02d} 已退场/死亡人物 {cid} 在 {c.get('scene_id')} 复出",
                            rel(d / "cards.yaml"))

        # K5 位置突变
        if prev_state and state:
            prev_chars = prev_state.get("characters") or {}
            for cid, cur in (state.get("characters") or {}).items():
                if not isinstance(cur, dict):
                    continue
                old = (prev_chars.get(cid) or {}).get("location")
                new = cur.get("location")
                if old and new and old != new:
                    if not (loc_in_text(old, script) or loc_in_text(new, script)):
                        warn("K5", f"{cid} 位置 e{prev_ep:02d}「{old}」→ e{ep:02d}「{new}」，"
                                   "剧本中未见过渡交代", rel(d / "script.md"))

            # K6 道具断链
            old_props = prev_state.get("props") or {}
            new_props = state.get("props") or {}
            for key, old_prop in old_props.items():
                if key in new_props:
                    continue
                status = str((old_prop or {}).get("status", ""))
                if any(x in status for x in ["消耗", "已归还", "归还", "丢弃", "交出", "回收", "清零"]):
                    continue
                warn("K6", f"道具 {key} 在 e{prev_ep:02d} 账本存在，e{ep:02d} 无处置地消失",
                     rel(d / "state.yaml"))

        # K4 伏笔挂账
        open_threads = [str(x) for x in (state or {}).get("open_threads") or []]
        for tid in open_threads:
            t = data["threads_by_id"].get(tid)
            if not t:
                blocker("K4", f"e{ep:02d} open_threads 含未登记伏笔 {tid}", rel(d / "state.yaml"))
                continue
            plant = as_int(t.get("planted_at"))
            payoff = as_int(t.get("planned_payoff"))
            if ep < plant:
                blocker("K4", f"e{ep:02d} 提前挂账伏笔 {tid}（计划 e{plant:02d} 埋设）",
                        rel(d / "state.yaml"))
            if payoff and ep > payoff:
                warn("K4", f"e{ep:02d} 仍挂账伏笔 {tid}，已过计划回收 e{payoff:02d}",
                     rel(d / "state.yaml"))
        for t in data["threads"]:
            tid = str(t.get("id"))
            if as_int(t.get("planted_at")) == ep and tid not in open_threads:
                warn("K4", f"e{ep:02d} 是伏笔 {tid} 的埋设集，但 open_threads 未挂账",
                     rel(d / "state.yaml"))

        # K7 时长
        if script:
            est = cjk_len(script) / 4.5
            if est > data["target"] * 1.2 or est < data["target"] * 0.5:
                warn("K7", f"e{ep:02d} 剧本约 {est:.1f}s，超出 {data['target']}s ±20% 区间",
                     rel(d / "script.md"))

        # K8 评审
        if script:
            if not review:
                warn("K8", f"e{ep:02d} 有剧本但缺 review.yaml", rel(d / "review.yaml"))
            else:
                calc = review_total(review)
                if review.get("total") is not None and as_int(review.get("total")) != calc:
                    warn("K8", f"e{ep:02d} review.total={review.get('total')} 与 8 维合计 {calc} 不一致",
                         rel(d / "review.yaml"))
                blockers = [i for i in (review.get("issues") or [])
                            if isinstance(i, dict) and i.get("severity") == "blocker"
                            and not i.get("resolved_after_review")]
                if review.get("verdict") == "approved" and blockers:
                    warn("K8", f"e{ep:02d} 标记 approved，但仍有 {len(blockers)} 条 blocker",
                         rel(d / "review.yaml"))

        if state:
            prev_state = state
            prev_ep = ep
            for cid, c in (state.get("characters") or {}).items():
                if isinstance(c, dict) and (c.get("dead") or c.get("written_out")):
                    dead.add(cid)


# ---------------------------------------------------------------- 渲染
def render(data: dict) -> str:
    title = str(data["cfg"].get("title") or "未命名项目")
    eps = data["episodes"]
    lines: list[str] = []
    lines.append(f"# 《{title}》连续性巡检与集末状态账本")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ "
                 f"项目：`{rel(data['proj'])}` ｜ 只读汇总，事实源仍是 episodes/*/state.yaml")
    lines.append("")

    blockers = [i for i in issues if i["level"] == "BLOCKER"]
    warns = [i for i in issues if i["level"] == "WARN"]
    lines.append("## 总览")
    lines.append("")
    lines.append("| 项 | 值 |")
    lines.append("|---|---|")
    lines.append(f"| 已进入制作的集 | {len(eps)} / {data['n']} |")
    lines.append(f"| BLOCKER | {len(blockers)} |")
    lines.append(f"| WARN | {len(warns)} |")
    lines.append(f"| 判定 | {'通过（无阻断矛盾）' if not blockers else '未通过'} |")
    lines.append("")

    lines.append("## 集末状态账本")
    lines.append("")
    lines.append("| 集 | 剧本秒 | 评审 | 人物位置 | 道具数 | open_threads |")
    lines.append("|---|---|---|---|---|---|")
    for e in eps:
        st = e["state"] or {}
        chars = st.get("characters") or {}
        locs = "；".join(f"{cid}:{c.get('location', '—')}"
                        for cid, c in chars.items() if isinstance(c, dict))
        r = e["review"] or {}
        review = (f"{r.get('total', '—')}/{r.get('threshold', '—')} {r.get('verdict', '—')}"
                  if r else "—")
        dur = f"{cjk_len(e['script']) / 4.5:.1f}" if e["script"] else "—"
        opens = ", ".join(map(str, st.get("open_threads") or [])) or "—"
        lines.append(f"| e{e['ep']:02d} | {dur} | {review} | {locs or '—'} | "
                     f"{len(st.get('props') or {})} | {opens} |")
    lines.append("")

    lines.append("## 人物位置轨迹")
    lines.append("")
    char_ids = sorted({cid for e in eps for cid in (e["state"] or {}).get("characters", {})})
    headers = ["人物"] + [f"e{e['ep']:02d}" for e in eps]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for cid in char_ids:
        row = [cid]
        for e in eps:
            c = ((e["state"] or {}).get("characters") or {}).get(cid) or {}
            row.append(str(c.get("location", "—")) if c else "—")
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## 道具账本")
    lines.append("")
    prop_keys = []
    for e in eps:
        for k in (e["state"] or {}).get("props") or {}:
            if k not in prop_keys:
                prop_keys.append(k)
    if prop_keys:
        lines.append("| 道具 | 首次 | 最近 | 当前状态 | 持有者 |")
        lines.append("|---|---|---|---|---|")
        for k in prop_keys:
            first = last = None
            cur = {}
            for e in eps:
                p = ((e["state"] or {}).get("props") or {}).get(k)
                if p:
                    first = first or e["ep"]
                    last = e["ep"]
                    cur = p
            lines.append(f"| {k} | e{first:02d} | e{last:02d} | "
                         f"{(cur or {}).get('status', '—')} | {(cur or {}).get('holder', '—')} |")
    else:
        lines.append("_暂无道具账本_")
    lines.append("")

    lines.append("## 伏笔挂账")
    lines.append("")
    if data["threads"]:
        lines.append("| ID | 埋设 | 回收 | 已挂账集 | 账本状态 |")
        lines.append("|---|---|---|---|---|")
        for t in data["threads"]:
            tid = str(t.get("id"))
            opens = [str(e["ep"]) for e in eps
                     if tid in [str(x) for x in (e["state"] or {}).get("open_threads") or []]]
            lines.append(f"| {tid} | e{as_int(t.get('planted_at')):02d} | "
                         f"e{as_int(t.get('planned_payoff')):02d} | "
                         f"{', '.join('e' + x.zfill(2) for x in opens) or '—'} | "
                         f"{t.get('status', '—')} |")
    else:
        lines.append("_threads.yaml 缺失_")
    lines.append("")

    lines.append("## 问题清单")
    lines.append("")
    if issues:
        for i in issues:
            lines.append(f"- [{i['level']}] {i['rule']} {i['msg']}"
                         + (f" ← {i['loc']}" if i["loc"] else ""))
    else:
        lines.append("- 未发现跨集 Continuity 问题。")
    lines.append("")

    lines.append("## 口径说明")
    lines.append("")
    lines.append("- K1/K2/K3/K4 为阻断级；K5-K8 为警告级，需人工确认。")
    lines.append("- 位置依据：新旧位置任一片段出现在本集剧本即视为有交代；标签可写细，剧本需有落点。")
    lines.append("- 道具断链：上集账本有、本集账本无，且状态未写消耗/归还/交出/回收/清零 → 警告。")
    lines.append("- 伏笔以 state.yaml 的 open_threads 为准，structure/threads.yaml 提供埋设/回收计划。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Story Lab 连续性巡检（只读）")
    ap.add_argument("slug", help="projects/<slug>")
    ap.add_argument("--write", action="store_true", help="写入 projects/<slug>/CONTINUITY.md")
    args = ap.parse_args()

    proj = ROOT / "projects" / args.slug
    if not proj.is_dir():
        print(f"项目不存在: {proj}", file=sys.stderr)
        return 1

    data = collect(proj)
    check_value_chain(data)
    check_episodes(data)
    text = render(data)
    print(text)

    if args.write:
        out = proj / "CONTINUITY.md"
        out.write_text(text + "\n", encoding="utf-8")
        print()
        print(f"已写入 {rel(out)}")

    blockers = [i for i in issues if i["level"] == "BLOCKER"]
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
