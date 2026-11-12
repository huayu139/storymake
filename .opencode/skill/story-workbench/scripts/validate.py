#!/usr/bin/env python3
"""Story Lab 确定性校验器（硬闸门）。

模型生成 → 本脚本把关 → 人裁决。脚本是唯一闸门，模型自查不算数。

用法:
    validate.py <slug> [--stage <阶段>] [--episode N]

退出码: 0 = 无 BLOCKER（可有 WARN）；1 = 存在 BLOCKER 或用法错误。
阶段: premise / characters / relations / structure / cards / script / review / all(默认)
规则编号见 references/continuity-rules.md（C*=阻断, W*=警告）。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# 仓库根目录：本脚本位于 .opencode/skill/story-workbench/scripts/
ROOT = Path(__file__).resolve().parents[4]
SKILL_DIR = Path(__file__).resolve().parents[1]

issues: list[dict] = []  # 统一收集


def blocker(rule: str, msg: str, loc: str = "") -> None:
    issues.append({"level": "BLOCKER", "rule": rule, "msg": msg, "loc": loc})


def warn(rule: str, msg: str, loc: str = "") -> None:
    issues.append({"level": "WARN", "rule": rule, "msg": msg, "loc": loc})


def load_yaml(path: Path):
    """读 YAML，失败时记 blocker 并返回 None。"""
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 — 解析错误本身就是问题
        blocker("YAML-PARSE", f"{path.name} 解析失败: {e}", str(path))
        return None


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def cjk_len(text: str) -> int:
    """中文按字、英文按词估算长度。"""
    cjk = len(re.findall(r"[一-鿿]", text))
    words = len(re.findall(r"[A-Za-z]+", text))
    return cjk + words


# 指令块：【场景】标签行及其后的描述段（到下一个节拍/场次为止）、【人物】标签行。
# 这些是给摄影、美术、演员看的**说明**，不占表演时长，估算台词时长时必须扣除。
_DIRECTIVE_RE = re.compile(
    r"^【场景】.*?(?=^【节拍|^## |\Z)"   # 【场景】块
    r"|^【人物】[^\n]*\n?",               # 【人物】行
    flags=re.S | re.M,
)


def performance_text(text: str) -> str:
    """去掉场景/人物描述指令块后的表演正文（用于时长估算与桥段扫描）。"""
    return _DIRECTIVE_RE.sub("", text or "")


# ---------------------------------------------------------------- S1 立意
def check_premise(proj: Path) -> None:
    p = proj / "bible/premise.md"
    text = load_text(p)
    if not text:
        blocker("C0-missing", "bible/premise.md 不存在（S1 未完成）", str(p))
        return
    for key, label in [("Logline", "logline"), ("引擎", "设定引擎")]:
        if key not in text:
            blocker("C7-missing", f"premise.md 缺少「{key}」章节", str(p))
    # 五要素粗查：主角/欲望/阻碍至少出现
    for kw in ["主角", "欲望", "阻碍"]:
        if kw not in text:
            warn("C7-missing", f"premise.md 未提及「{kw}」，确认五要素齐全", str(p))
    check_cliches(text, str(p))


# ---------------------------------------------------------------- S2 人物
REQUIRED_CHAR_FIELDS = ["want", "fear", "secret", "lie", "wound", "arc"]
# 可拍的形象四件套：个性/外表/穿着/特征（剧本首次出场的【人物】行要与它一致）
REQUIRED_CHAR_DESC_FIELDS = ["persona", "appearance", "wardrobe", "signature"]
MIN_CHAR_DESC = 6  # 每项至少 6 个汉字，太短等于没写


def load_characters(proj: Path) -> dict[str, dict]:
    chars = {}
    cdir = proj / "bible/characters"
    if not cdir.exists():
        return chars
    for f in sorted(cdir.glob("*.yaml")):
        c = load_yaml(f)
        if isinstance(c, dict) and c.get("id"):
            chars[c["id"]] = c
        else:
            blocker("YAML-PARSE", f"{f.name} 缺 id 或格式错误", str(f))
    return chars


def check_characters(proj: Path) -> dict[str, dict]:
    chars = load_characters(proj)
    if len(chars) < 3:
        blocker("C0-missing", f"人物卡不足 3 份（当前 {len(chars)}），S2 未完成",
                str(proj / "bible/characters"))
    for cid, c in chars.items():
        loc = f"bible/characters/{cid}.yaml"
        for f in REQUIRED_CHAR_FIELDS:
            if not c.get(f):
                blocker("C7-missing", f"人物 {cid} 缺字段 {f}", loc)
        vs = c.get("voice_samples") or []
        if len(vs) < 3:
            blocker("C7-missing", f"人物 {cid} voice_samples 少于 3 句（当前 {len(vs)}）", loc)
        ns = c.get("never_say") or []
        if len(ns) < 2:
            blocker("C7-missing", f"人物 {cid} never_say 少于 2 句（当前 {len(ns)}）", loc)
        if not c.get("voice_rules"):
            warn("C7-missing", f"人物 {cid} 缺 voice_rules（声音规则）", loc)
        # C11 形象四件套：个性/外表/穿着/特征（QC 硬闸门）
        for f in REQUIRED_CHAR_DESC_FIELDS:
            v = str(c.get(f) or "").strip()
            if not v:
                blocker("C11-card-persona", f"人物 {cid} 缺「{f}」描述", loc)
            elif cjk_len(v) < MIN_CHAR_DESC:
                blocker("C11-card-persona",
                        f"人物 {cid} 的「{f}」仅 {cjk_len(v)} 字（至少 {MIN_CHAR_DESC} 字）", loc)
    return chars


# ---------------------------------------------------------------- S3 关系
def check_relations(proj: Path, chars: dict[str, dict]) -> list[dict]:
    rels = load_yaml(proj / "bible/relations.yaml")
    if rels is None:
        blocker("C0-missing", "bible/relations.yaml 不存在（S3 未完成）", str(proj))
        return []
    if not isinstance(rels, list) or not rels:
        blocker("C0-missing", "relations.yaml 为空", str(proj / "bible/relations.yaml"))
        return []
    loc = "bible/relations.yaml"
    # 两两有边（C8 附带：三角基本盘）
    ids = set(chars)
    touched = set()
    for i, r in enumerate(rels):
        for f in ["from", "to", "power_diff", "dependency", "unsaid", "tension"]:
            if not r.get(f):
                blocker("C8-missing", f"关系 #{i} 缺字段 {f}", loc)
        a, b = r.get("from"), r.get("to")
        if a in ids:
            touched.add(a)
        else:
            blocker("C8", f"关系 #{i} from={a} 不是已存在的人物 id", loc)
        if b in ids:
            touched.add(b)
        else:
            blocker("C8", f"关系 #{i} to={b} 不是已存在的人物 id", loc)
        pd = str(r.get("power_diff", ""))
        if any(x in pd for x in ["均等", "对称", "势均力敌"]):
            blocker("C8", f"关系 #{i} power_diff 必须不对称（当前: {pd}）", loc)
    missing = ids - touched
    if missing:
        blocker("C8", f"人物 {sorted(missing)} 与任何人无关系边", loc)
    return rels if isinstance(rels, list) else []


# ---------------------------------------------------------------- S4 结构
CLIFF_TYPES = {"揭露", "反转", "倒计时", "闯入"}


def check_structure(proj: Path, n_episodes: int) -> tuple[list[dict], dict[int, dict]]:
    hooks = load_yaml(proj / "structure/hooks.yaml")
    threads = load_yaml(proj / "structure/threads.yaml")
    movements = load_yaml(proj / "structure/movements.yaml")
    loc_h = "structure/hooks.yaml"

    if hooks is None or threads is None or movements is None:
        blocker("C0-missing", "structure/ 下 movements/hooks/threads 缺失（S4 未完成）",
                str(proj / "structure"))
        return [], {}

    if not isinstance(hooks, list) or len(hooks) < n_episodes:
        blocker("C0-missing", f"钩子表集数不足（{len(hooks) if isinstance(hooks, list) else 0}/{n_episodes}）",
                loc_h)
        return [], {}

    by_ep: dict[int, dict] = {}
    for h in hooks:
        ep = h.get("episode")
        if ep is None:
            blocker("C6", "钩子缺 episode 字段", loc_h)
            continue
        by_ep[ep] = h
        if not h.get("question_left_open"):
            blocker("C6", f"第 {ep} 集 question_left_open 为空（结尾无悬念=废集）", loc_h)
        if h.get("cliffhanger_type") not in CLIFF_TYPES:
            blocker("C6", f"第 {ep} 集 cliffhanger_type 非法: {h.get('cliffhanger_type')}", loc_h)
        if h.get("value_before") == h.get("value_after"):
            blocker("C3", f"第 {ep} 集 value_before == value_after（集级无价值翻转）", loc_h)

    # 相邻集悬念类型不得重复（C6）；最近 3 集相同给 W2
    eps = sorted(by_ep)
    for a, b in zip(eps, eps[1:]):
        if b == a + 1 and by_ep[a].get("cliffhanger_type") == by_ep[b].get("cliffhanger_type"):
            blocker("C6", f"第 {a}/{b} 集悬念类型重复: {by_ep[a].get('cliffhanger_type')}", loc_h)
    for i in range(len(eps) - 2):
        trio = [by_ep[e].get("cliffhanger_type") for e in eps[i:i + 3]]
        if len(set(trio)) == 1:
            warn("W2", f"第 {eps[i]}-{eps[i + 2]} 集悬念类型连续 3 集相同: {trio[0]}", loc_h)
    # 四类都要出现（季级）
    used = {by_ep[e].get("cliffhanger_type") for e in eps}
    if len(CLIFF_TYPES - used) > 0 and len(eps) >= 4:
        warn("W2", f"本季未使用的悬念类型: {sorted(CLIFF_TYPES - used)}", loc_h)

    # 伏笔时序（C2）+ 超期（W1）
    loc_t = "structure/threads.yaml"
    # W1 以"已写到第几集"为基准：规划阶段没有剧本则不报超期
    latest_ep = 0
    for i in range(1, n_episodes + 1):
        if (proj / f"episodes/e{i:02d}/script.md").exists():
            latest_ep = i
    if not isinstance(threads, list):
        blocker("YAML-PARSE", "threads.yaml 应为数组", loc_t)
        return hooks, by_ep
    for t in threads:
        tid = t.get("id", "?")
        planted, payoff = t.get("planted_at"), t.get("planned_payoff")
        if planted is None or payoff is None:
            blocker("C2", f"伏笔 {tid} 缺 planted_at/planned_payoff", loc_t)
            continue
        if payoff <= planted:
            blocker("C2", f"伏笔 {tid} 先回收后埋 (planted={planted} >= payoff={payoff})", loc_t)
        st = t.get("status", "planted")
        if st == "dropped" and not t.get("dropped_reason"):
            blocker("C2", f"伏笔 {tid} dropped 但无理由", loc_t)
        if st == "planted" and latest_ep - planted >= 3:
            warn("W1", f"伏笔 {tid} 已 {latest_ep - planted} 集未推进", loc_t)
    # 大结局前主线伏笔须有回收安排
    if isinstance(threads, list):
        for t in threads:
            if t.get("status") in ("planted", "building") and \
               (t.get("planned_payoff") or 0) > n_episodes:
                warn("W1", f"伏笔 {t.get('id')} 计划回收集超出季长", loc_t)

    # 钉死集
    pinned = (movements or {}).get("pinned_episodes") or []
    if len(pinned) < 4:
        warn("W2", f"钉死集仅 {len(pinned)} 个（建议 4: 付费卡点/中点/一无所有/大结局）",
             "structure/movements.yaml")
    return hooks, by_ep


# ---------------------------------------------------------------- S5 场景卡
def check_cards(proj: Path, chars: dict[str, dict], ep: int,
                hooks_by_ep: dict[int, dict], dead: set[str], visible_up_to: int) -> list[dict]:
    f = proj / f"episodes/e{ep:02d}/cards.yaml"
    cards = load_yaml(f)
    if cards is None:
        blocker("C0-missing", f"episodes/e{ep:02d}/cards.yaml 不存在（S5 未完成）", str(f))
        return []
    if not isinstance(cards, list) or not cards:
        blocker("C0-missing", "cards.yaml 为空", str(f))
        return []
    loc = str(f)
    for c in cards:
        sid = c.get("scene_id", "?")
        # C3 价值翻转
        if not c.get("value_before") or not c.get("value_after"):
            blocker("C3", f"{sid} 缺 value_before/value_after", loc)
        elif c["value_before"] == c["value_after"]:
            blocker("C3", f"{sid} 价值无翻转 (value_before == value_after)", loc)
        # 角色 id / 死人 / 可见性
        for cid in c.get("cast") or []:
            if cid not in chars:
                blocker("C8", f"{sid} cast 含未知人物 {cid}", loc)
                continue
            if cid in dead and not c.get("flashback"):
                blocker("C1", f"{sid} 已退场/死亡人物 {cid} 出场且未标 flashback", loc)
            vf = chars[cid].get("visible_from", 1)
            if vf > ep and not c.get("flashback"):
                blocker("C5", f"{sid} 人物 {cid} visible_from={vf}，第 {ep} 集不可见", loc)
        for f_ in ["objective", "obstacle", "turn", "information_delta", "must_happen"]:
            if not c.get(f_):
                blocker("C7", f"{sid} 缺字段 {f_}", loc)
        if c.get("estimated_seconds", 0) > 90:
            warn("W6", f"{sid} 预估 {c.get('estimated_seconds')}s 偏长", loc)

        # ---- C10 场景视觉三件套（QC 硬闸门）----
        sd = str(c.get("scene_description") or "").strip()
        if not sd:
            blocker("C10-card-scene", f"{sid} 缺 scene_description（场景详细描述）", loc)
        elif cjk_len(sd) < 20:
            blocker("C10-card-scene",
                    f"{sid} scene_description 仅 {cjk_len(sd)} 字（至少 20 字，写时间/地点/物件/风格）", loc)
        props = c.get("props")
        if not isinstance(props, list) or not props:
            blocker("C10-card-props", f"{sid} 缺 props（本场关键物件清单，至少 1 件）", loc)
        else:
            for p in props:
                if not isinstance(p, dict) or not str(p.get("name") or "").strip():
                    blocker("C10-card-props", f"{sid} 的 props 含缺 name 的条目: {p!r}", loc)
                elif not str(p.get("id") or "").strip():
                    blocker("C10-card-props", f"{sid} 的 props「{p.get('name')}」缺 id", loc)
        beats = c.get("visual_beats")
        if not isinstance(beats, list) or len(beats) < 2:
            blocker("C10-card-beats",
                    f"{sid} visual_beats 需 ≥2 条（当前 {len(beats) if isinstance(beats, list) else 0}）", loc)
    # 末场悬念与钩子一致
    last, h = cards[-1], hooks_by_ep.get(ep)
    if h:
        ct_last = last.get("cliffhanger_type")
        if not ct_last:
            blocker("C6", f"第 {ep} 集末场缺 cliffhanger_type", loc)
        elif ct_last != h.get("cliffhanger_type"):
            blocker("C6", f"第 {ep} 集末场悬念 {ct_last} ≠ 钩子表 {h.get('cliffhanger_type')}", loc)
    return cards


# ---------------------------------------------------------------- S6 剧本
def split_scenes(text: str) -> list[tuple[str, str]]:
    """按「## 场景 」切成 [(标题, 场景块)]，第一块片头会被丢弃。"""
    parts = re.split(r"(?m)^(?=## 场景 )", text or "")
    out: list[tuple[str, str]] = []
    for i, p in enumerate(parts):
        if i == 0 and not p.lstrip().startswith("## 场景"):
            continue
        first = p.splitlines()[0].strip() if p.strip() else ""
        out.append((first, p))
    return out


def match_char(display: str, chars: dict[str, dict]) -> str | None:
    """在场人物行的显示名 → 人物卡 id（name / 括号前基名 / aliases / 子串）。"""
    d = (display or "").strip()
    if not d:
        return None
    for cid, c in chars.items():
        nm = str(c.get("name") or "")
        base = re.split(r"[（(]", nm)[0].strip()
        if d == nm or d == base:
            return cid
        for a in c.get("aliases") or []:
            if d == str(a).strip():
                return cid
    for cid, c in chars.items():
        nm = str(c.get("name") or "")
        base = re.split(r"[（(]", nm)[0].strip()
        if d in nm or (base and base in d):
            return cid
        for a in c.get("aliases") or []:
            if str(a).strip() and str(a).strip() in d:
                return cid
    return None


SCENE_TAGS = ("时间", "地点", "物件", "风格")
CHAR_TAGS = ("个性", "外表", "穿着", "特征")


def _tag_value(line: str, tag: str) -> str:
    """取「标签：值」的值；支持全角/半角冒号与 ｜ 分隔。"""
    m = re.search(rf"{tag}[：:]\s*([^｜|【\n]*)", line)
    return (m.group(1) if m else "").strip()


def _check_visual_qc(text: str, chars: dict[str, dict], loc: str) -> None:
    """C10 场景描述 + C11 人物描述的剧本侧检查。"""
    scenes = split_scenes(text)
    if not scenes:
        blocker("C10-script-scene", "剧本没有任何「## 场景 」段落", loc)
        return
    if not chars:
        blocker("C0-missing", "人物卡缺失，无法校验【人物】描述", loc)
        return

    seen: set[str] = set()   # 本集已出场角色（含描述）
    for i, (title, block) in enumerate(scenes, 1):
        # ---------- 场景：【场景】行 + 四要素 + 描述段 ----------
        m = re.search(r"^(【场景】[^\n]*)\n?(.*?)(?=^【节拍|^## |\Z)",
                      block, flags=re.S | re.M)
        if not m:
            blocker("C10-script-scene",
                    f"{title or '场景 ' + str(i)} 缺【场景】行（时间/地点/物件/风格 + 可拍描述）", loc)
        else:
            head, body = m.group(1), m.group(2)
            for tag in SCENE_TAGS:
                v = _tag_value(head, tag)
                if not v:
                    blocker("C10-script-scene-tags",
                            f"{title or '场景 ' + str(i)} 的【场景】行缺「{tag}：」", loc)
                elif cjk_len(v) < 2:
                    blocker("C10-script-scene-tags",
                            f"{title or '场景 ' + str(i)} 的「{tag}」内容过短", loc)
            if cjk_len(body) < 30:
                blocker("C10-script-scene-body",
                        f"{title or '场景 ' + str(i)} 场景描述仅 {cjk_len(body)} 字"
                        f"（标签之外还需 ≥30 字可拍描述）", loc)

        # ---------- 人物：本集首次出场必须有【人物】行 ----------
        persona_lines = [ln.strip() for ln in block.splitlines()
                         if ln.strip().startswith("【人物】")]
        first_in_scene: dict[str, str] = {}   # cid -> 显示名
        # 只认紧跟场景标题的那一个括号行（其余（…）是动作/字幕说明）
        cast_line = ""
        blines = block.splitlines()
        for k, ln in enumerate(blines):
            s = ln.strip()
            if s.startswith("（") and s.endswith("）"):
                if k and blines[k - 1].strip().startswith("## 场景"):
                    cast_line = s[1:-1]
                break
        for name in re.split(r"[、,，·/]", cast_line):
            name = name.strip()
            if not name:
                continue
            cid = match_char(name, chars)
            if not cid:
                warn("W10-name", f"{title or '场景 ' + str(i)} 在场人物「{name}」"
                                 f"未匹配到人物卡（补 aliases 或核对 name）", loc)
                continue
            if cid not in seen:
                first_in_scene.setdefault(cid, name)

        for cid, display in first_in_scene.items():
            nm = str(chars[cid].get("name") or display)
            base = re.split(r"[（(]", nm)[0].strip()
            hit = next((ln for ln in persona_lines
                        if base in ln or display in ln), None)
            if hit is None:
                blocker("C11-script-persona",
                        f"{title or '场景 ' + str(i)} 中「{display}」本集首次出场，"
                        f"缺【人物】行（个性/外表/穿着/特征）", loc)
            else:
                for tag in CHAR_TAGS:
                    v = _tag_value(hit, tag)
                    if not v:
                        blocker("C11-script-persona-tags",
                                f"{title or '场景 ' + str(i)} 的【人物】{display} 缺「{tag}：」", loc)
                    elif cjk_len(v) < 2:
                        blocker("C11-script-persona-tags",
                                f"{title or '场景 ' + str(i)} 的【人物】{display}「{tag}」内容过短", loc)
            seen.add(cid)


def collect_dead(proj: Path, up_to_ep: int) -> set[str]:
    """从 e01..e{up_to_ep-1} 的 state.yaml 收集 dead/written_out 人物。"""
    dead = set()
    for i in range(1, up_to_ep):
        st = load_yaml(proj / f"episodes/e{i:02d}/state.yaml")
        if not isinstance(st, dict):
            continue
        for cid, c in (st.get("characters") or {}).items():
            if isinstance(c, dict) and (c.get("dead") or c.get("written_out")):
                dead.add(cid)
    return dead


def check_script(proj: Path, chars: dict[str, dict], ep: int, hooks_by_ep: dict[int, dict],
                 prev_state: dict) -> None:
    f = proj / f"episodes/e{ep:02d}/script.md"
    text = load_text(f)
    if not text:
        blocker("C0-missing", f"episodes/e{ep:02d}/script.md 不存在（S6 未完成）", str(f))
        return
    loc = str(f)

    # ---- C10/C11 场景与人物描述（QC 硬闸门）----
    _check_visual_qc(text, chars, loc)

    # C4 信息泄露：must_not_know / hidden 字面出现在台词中
    # （确定性脚本能拦直接陈述；语义层面的泄露由 S7 subagent 评审覆盖）
    leaks = []
    for cid, c in chars.items():
        for s in (c.get("must_not_know") or []):
            if s and s in text:
                leaks.append(f"{cid} 的 must_not_know「{s}」")
    st = load_yaml(proj / f"episodes/e{ep:02d}/state.yaml")
    if isinstance(st, dict):
        for cid, c in (st.get("characters") or {}).items():
            if isinstance(c, dict):
                for s in (c.get("must_not_know") or []):
                    if s and s in text:
                        leaks.append(f"{cid} 的 must_not_know「{s}」")
    cards = load_yaml(proj / f"episodes/e{ep:02d}/cards.yaml") or []
    for c in cards if isinstance(cards, list) else []:
        hidden = (c.get("information_delta") or {}).get("hidden")
        if hidden and hidden in text:
            leaks.append(f"{c.get('scene_id')} 的 hidden「{hidden}」")
    for L in leaks:
        blocker("C4", f"信息泄露: {L}", loc)

    # C6 结尾必须留下本集问题
    h = hooks_by_ep.get(ep)
    if h and h.get("question_left_open"):
        tail = text[-300:]  # 结尾 300 字内至少要出现悬念要素（关键词提示）
        q = h["question_left_open"]
        key = re.sub(r"[？?。]", "", q)[:4]  # 取问题前 4 字做提示
        if key and key not in tail and q not in text:
            warn("C6", f"剧本结尾未见悬念要素「{key}…」，确认末 5 秒钩子已落实", loc)

    # W4 AI 味
    cliches = json.loads((SKILL_DIR / "config/cliches.json").read_text(encoding="utf-8"))
    for w in cliches.get("ai_isms", []):
        if w in text:
            warn("W4", f"AI 命中「{w}」", loc)
    # W5 桥段黑名单
    check_cliches(text, loc)
    # W6 时长（4.5 字/秒；场景/人物描述是给制作看的说明，不计入表演时长）
    proj_cfg = load_yaml(proj / "project.yaml") or {}
    seconds = proj_cfg.get("seconds_per_episode", 90)
    est = cjk_len(performance_text(text)) / 4.5
    if est > seconds * 1.2 or est < seconds * 0.5:
        warn("W6", f"预估时长 {est:.0f}s，目标 {seconds}s（±20% 外）", loc)

    # W7 上一集状态 vs 本集：人物位置突变提醒（需一句交代）
    if isinstance(prev_state, dict):
        for cid, pc in (prev_state.get("characters") or {}).items():
            if not isinstance(pc, dict):
                continue
            old_loc = pc.get("location")
            new_st = load_yaml(proj / f"episodes/e{ep:02d}/state.yaml") or {}
            nc = (new_st.get("characters") or {}).get(cid)
            if isinstance(nc, dict) and old_loc and nc.get("location") and \
               nc["location"] != old_loc and nc["location"] not in text and old_loc not in text:
                warn("W7", f"{cid} 位置 {old_loc} → {nc['location']}，剧本中未见过渡交代", loc)

    # 集末状态必须存在（下一集的输入）
    if not (proj / f"episodes/e{ep:02d}/state.yaml").exists():
        blocker("C0-missing", f"episodes/e{ep:02d}/state.yaml 缺失（S6 未完成）", loc)


# ---------------------------------------------------------------- S7 评审
REVIEW_DIMS = ["hook", "causality", "character_consistency", "voice_distinctness",
               "value_shift", "information_management", "emotional_payoff", "originality"]


def check_review(proj: Path, ep: int) -> None:
    f = proj / f"episodes/e{ep:02d}/review.yaml"
    r = load_yaml(f)
    if r is None:
        blocker("C0-missing", f"episodes/e{ep:02d}/review.yaml 不存在（S7 未完成）", str(f))
        return
    loc = str(f)
    scores = r.get("scores") or {}
    total = 0
    for d in REVIEW_DIMS:
        s = scores.get(d)
        if not isinstance(s, dict) or not s.get("score"):
            blocker("C7", f"评审缺维度 {d} 或分数", loc)
            continue
        if not s.get("evidence"):
            blocker("C7", f"评审维度 {d} 缺 evidence（分数必须引用原文）", loc)
        if not 1 <= int(s["score"]) <= 5:
            blocker("C7", f"评审维度 {d} 分数越界: {s['score']}", loc)
        total += int(s["score"])
    if r.get("total") not in (None, total) and scores:
        warn("C7", f"total 字段 {r.get('total')} ≠ 实际合计 {total}", loc)
    verdict = r.get("verdict")
    if verdict not in ("approved", "needs_revision"):
        blocker("C7", f"verdict 非法: {verdict}", loc)
    if verdict == "approved" and any(i.get("severity") == "blocker" for i in r.get("issues") or []):
        blocker("C7", "存在 blocker 却标记 approved", loc)
    if verdict == "needs_revision" and not r.get("fix_top3"):
        warn("C7", "needs_revision 但 fix_top3 为空，修复无目标", loc)


# ---------------------------------------------------------------- 通用
def check_cliches(text: str, loc: str) -> None:
    data = json.loads((SKILL_DIR / "config/cliches.json").read_text(encoding="utf-8"))
    for c in data.get("banned", []):
        if c["name"] in text:
            warn("W5", f"桥段黑名单命中「{c['name']}」({c.get('note', '')})", loc)


def check_decisions(proj: Path) -> None:
    f = proj / "decisions.jsonl"
    if not f.exists():
        warn("W7", "decisions.jsonl 不存在（尚无决策记录）", str(f))
        return
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if "stage" not in d or "action" not in d:
                blocker("YAML-PARSE", f"decisions.jsonl 第 {i} 行缺 stage/action", str(f))
        except json.JSONDecodeError as e:
            blocker("YAML-PARSE", f"decisions.jsonl 第 {i} 行非法 JSON: {e}", str(f))


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description="Story Lab 确定性校验器")
    ap.add_argument("slug", help="projects/<slug>")
    ap.add_argument("--stage", default="all",
                    choices=["all", "premise", "characters", "relations", "structure",
                             "cards", "script", "review"])
    ap.add_argument("--episode", type=int, default=None, help="阶段为 cards/script/review 时必填")
    args = ap.parse_args()

    proj = ROOT / "projects" / args.slug
    if not proj.is_dir():
        print(f"[BLOCKER] 项目不存在: {proj}", file=sys.stderr)
        return 1

    cfg = load_yaml(proj / "project.yaml") or {}
    n_eps = int(cfg.get("episodes", 1))
    ep = args.episode

    stage = args.stage
    if stage in ("cards", "script", "review") and ep is None:
        print("[BLOCKER] --stage cards/script/review 需要 --episode N", file=sys.stderr)
        return 1

    # 各阶段按依赖顺序执行（all 时全跑，前面缺文件会报 blocker，符合预期）
    chars: dict[str, dict] = {}
    hooks_by_ep: dict[int, dict] = {}

    if stage in ("all", "premise"):
        check_premise(proj)
    if stage in ("all", "characters"):
        chars = check_characters(proj)
    elif stage in ("cards", "script", "review"):
        chars = load_characters(proj)  # 依赖人物卡做 C1/C4/C5

    if stage in ("all", "relations"):
        check_relations(proj, chars or load_characters(proj))
    if stage in ("all", "structure"):
        _, hooks_by_ep = check_structure(proj, n_eps)
    elif stage in ("cards", "script"):
        _, hooks_by_ep = check_structure(proj, n_eps)

    if stage in ("all", "cards"):
        eps = [ep] if ep else range(1, n_eps + 1)
        dead_seen: set[str] = set()
        for e in eps:
            dead_seen |= collect_dead(proj, e)
            check_cards(proj, chars, e, hooks_by_ep, dead_seen, visible_up_to=e)
    if stage in ("all", "script"):
        eps = [ep] if ep else range(1, n_eps + 1)
        dead_seen = set()
        for e in eps:
            dead_seen |= collect_dead(proj, e)
            prev = load_yaml(proj / f"episodes/e{e - 1:02d}/state.yaml") if e > 1 else {}
            check_script(proj, chars, e, hooks_by_ep, prev or {})
    if stage in ("all", "review"):
        eps = [ep] if ep else range(1, n_eps + 1)
        for e in eps:
            check_review(proj, e)

    if stage in ("all",):
        check_decisions(proj)

    # 输出
    blockers = [i for i in issues if i["level"] == "BLOCKER"]
    warns = [i for i in issues if i["level"] == "WARN"]
    for i in issues:
        print(f"[{i['level']}] {i['rule']} {i['msg']}" + (f"  ← {i['loc']}" if i["loc"] else ""))
    print(f"\n结果: {len(blockers)} blocker, {len(warns)} warn")
    if not blockers:
        print("OK — 无阻断问题" + ("（有警告需知情）" if warns else ""))
    return 1 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
