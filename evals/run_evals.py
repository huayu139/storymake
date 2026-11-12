#!/usr/bin/env python3
"""Story Lab 回归用例：修改 skill 后必跑，全绿才算改完。

原理：在 projects/__eval_trap__/ 下程序化构造"带陷阱的故事产物"，
运行 validate.py，断言每类违规都被检出；再构造一个干净项目断言 0 blocker。

用法: run_evals.py
退出码: 0 = 全绿；1 = 有回归。
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".opencode/skill/story-workbench"
VALIDATE = SKILL / "scripts/validate.py"
STATUS = SKILL / "scripts/status.py"
CONTINUITY = SKILL / "scripts/continuity.py"
OVERVIEW = SKILL / "scripts/overview.py"
PY = sys.executable
SLUG = "__eval_trap__"
PROJ = ROOT / "projects" / SLUG

results: list[tuple[str, bool, str]] = []


def run_validate(*extra: str) -> tuple[int, str]:
    r = subprocess.run([PY, str(VALIDATE), SLUG, *extra],
                       capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def run_status(*extra: str) -> tuple[int, str]:
    r = subprocess.run([PY, str(STATUS), SLUG, *extra],
                       capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def run_continuity(*extra: str) -> tuple[int, str]:
    r = subprocess.run([PY, str(CONTINUITY), SLUG, *extra],
                       capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def run_overview(*extra: str) -> tuple[int, str]:
    r = subprocess.run([PY, str(OVERVIEW), SLUG, *extra],
                       capture_output=True, text=True, cwd=str(ROOT))
    return r.returncode, r.stdout + r.stderr


def write(path: Path, content) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        path.write_text(yaml.safe_dump(content, allow_unicode=True), encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")


def expect(rule: str, out: str, should_fire: bool = True, case: str = "") -> None:
    fired = any(
        f"[BLOCKER] {rule} " in ln or f"[BLOCKER] {rule}-" in ln or
        f"[WARN] {rule} " in ln or f"[WARN] {rule}-" in ln
        for ln in out.splitlines())
    ok = fired == should_fire
    results.append((f"{case}:{rule}", ok,
                    "" if ok else f"应{'触发' if should_fire else '不触发'}"
                    f"但{'触发了' if fired else '未触发'}"))


def base_project(n_episodes: int = 2) -> None:
    """构造一个结构完整、仅缺剧本细节的基础项目。"""
    if PROJ.exists():
        shutil.rmtree(PROJ)
    write(PROJ / "project.yaml", {
        "slug": SLUG, "genre": "都市逆袭", "platform": "竖屏短剧",
        "episodes": n_episodes, "seconds_per_episode": 90,
        "audience": "25-35", "taboos": [],
    })
    write(PROJ / "bible/premise.md", """# 前提 Premise

## Logline
妹妹在姐姐的行车记录仪里发现姐夫的秘密，她决定用 7 天时间拿到存储卡。

## 设定引擎
行车记录仪每天自动覆盖，主角必须在覆盖前拿到卡——可持续 30 个转折。

## 五要素
主角：林晚（妹妹）  欲望：真相  阻碍：顾彦辰抢先  反转：姐夫不是凶手  引擎：7 天覆盖倒计时
""")
    for i, (cid, nm) in enumerate([("lin-wan", "林晚"), ("gu-yanchen", "顾彦辰"), ("zhao-li", "赵莉")]):
        write(PROJ / f"bible/characters/{cid}.yaml", {
            "id": cid, "name": nm,
            "role": ["protagonist", "antagonist", "supporting"][i],
            "want": "拿到存储卡", "fear": "真相毁掉家人", "secret": "隐瞒了通话记录",
            "lie": "我只是想查清楚", "wound": "姐姐车祸当晚没接电话",
            "arc": "从逃避到直面",
            "persona": "信证据不信人，被噎住时反而更安静，逼到墙角才掀桌",
            "appearance": "28 岁偏瘦，眼下发青，指节有旧握笔茧，左眉尾一道小疤",
            "wardrobe": "男友风旧夹克袖口磨白，深色工装裤，背一个磨出毛边的电脑包",
            "signature": "说谎前先摸耳垂，说真话时直视对方不眨眼，无意识敲两下桌面",
            "voice_samples": ["我不要解释，我要证据。", "你早就知道了，对吧？",
                              "这卡里有什么，你比我清楚。", "别跟我谈感情，谈证据。",
                              "七天，我等得起。"],
            "voice_rules": ["短句", "不感叹"],
            "never_say": ["你听我解释", "我只是个外人"],
            "visible_from": 1, "version": 1,
        })
    write(PROJ / "bible/scenes.yaml", {
        "scenes": [
            {
                "id": "garage", "name": "地下车库",
                "aliases": ["地下车库", "地下库", "小区地下车库 B2 层"],
                "space": "冷白灯管一排，水泥柱与车位划线，电梯口指示灯",
                "lighting_anchor": "冷白灯管顶光偏硬",
                "palette_core": ["水泥灰", "冷白"],
                "ambience": "灯管嗡嗡、回声",
                "vertical": "竖屏：车位纵深，人物胸像",
            },
            {
                "id": "market-gate", "name": "菜市场大门口",
                "aliases": ["菜市场大门口", "市场入口"],
                "space": "卷帘门与公告栏，单宽通道，白炽灯次第亮",
                "lighting_anchor": "白炽灯顶光偏硬",
                "palette_core": ["水泥灰", "暖黄"],
                "ambience": "吆喝、卸货",
                "vertical": "竖屏：公告栏纵深",
            },
        ],
    })
    write(PROJ / "bible/relations.yaml", [
        {"from": "lin-wan", "to": "gu-yanchen", "type": "前恋人/对峙",
         "power_diff": "顾彦辰占优（信息）", "dependency": "林晚需要他的资源",
         "unsaid": "他三年前见过姐姐", "tension": "每次对话都试探", "flip_episode": 0},
        {"from": "lin-wan", "to": "zhao-li", "type": "闺蜜",
         "power_diff": "林晚占优（信任）", "dependency": "赵莉需要林晚的认可",
         "unsaid": "赵莉当晚在场", "tension": "关心里藏着试探", "flip_episode": 0},
        {"from": "gu-yanchen", "to": "zhao-li", "type": "旧识",
         "power_diff": "顾彦辰占优（秘密）", "dependency": "赵莉有求于他",
         "unsaid": "两人交换过信息", "tension": "客气下的合谋感", "flip_episode": 0},
    ])
    write(PROJ / "structure/movements.yaml", {
        "movements": [
            {"id": 1, "name": "铺垫", "episodes": [1], "goal": "建立常态与裂缝"},
            {"id": 2, "name": "升级", "episodes": [2], "goal": "主动出击"},
        ],
        "pinned_episodes": [
            {"episode": 1, "kind": "钩子"}, {"episode": 2, "kind": "大结局"},
            {"episode": 3, "kind": "中点"}, {"episode": 4, "kind": "一无所有"},
        ],
    })
    write(PROJ / "structure/hooks.yaml", [
        {"episode": 1, "movement": 1,
         "question_raised": "行车记录仪里为什么有姐夫？",
         "question_left_open": "谁把存储卡拿走了？",
         "cliffhanger_type": "揭露", "value_before": "信任", "value_after": "怀疑",
         "pinned": True},
        {"episode": 2, "movement": 2,
         "question_raised": "赵莉当晚到底在不在场？",
         "question_left_open": "录音笔会不会被发现？",
         "cliffhanger_type": "倒计时", "value_before": "怀疑", "value_after": "危险",
         "pinned": True},
    ])
    write(PROJ / "structure/threads.yaml", [
        {"id": "t-01", "type": "伏笔", "planted_at": 1, "planned_payoff": 2,
         "status": "planted", "description": "存储卡"},
    ])


def episode_shell(ep: int, cards: list, script: str, state: dict, review: dict) -> None:
    d = PROJ / f"episodes/e{ep:02d}"
    write(d / "cards.yaml", cards)
    write(d / "script.md", script)
    write(d / "state.yaml", state)
    write(d / "review.yaml", review)


def good_card(ep: int, dead_cast: list | None = None, value_same: bool = False) -> dict:
    return {
        "scene_id": f"e{ep:02d}-sc01", "pov": "lin-wan",
        "location": "地下车库", "time": "夜",
        "scene_ref": "garage",
        "shot_size": "中近景", "camera": "固定",
        "lighting": "冷白灯管顶光，柔",
        "palette": "水泥灰、冷白、暖黄灯影",
        "scene_description": (
            "深夜的地下车库 B2 层，冷白灯管嗡嗡响，只有她那辆车顶还积着一层灰。"
            "远处电梯口的指示灯是唯一的暖色，水泥地上留着两道新鲜轮胎印，"
            "风从坡道口灌进来，把塑料袋吹到车轮底下。"
        ),
        "props": [{"id": "dashcam", "name": "行车记录仪", "state": "被拿走",
                   "holder": "gu-yanchen"}],
        "visual_beats": ["车顶积灰被她擦掉一块，指印清晰",
                         "录音笔的红点在副驾一闪一闪"],
        "cast": dead_cast or ["lin-wan", "gu-yanchen"],
        "objective": "拿到行车记录仪", "obstacle": "顾彦辰先到一步",
        "value_before": "被动/被控制",
        "value_after": "被动/被控制" if value_same else "主动/掌握筹码",
        "must_happen": ["发现存储卡已被拿走"],
        "must_not_happen": ["不能揭露顾彦辰身份"],
        "information_delta": {"lin-wan": "确认隐瞒", "audience": "看到口袋的卡",
                              "hidden": "顾彦辰的真实身份"},
        "turn": "她假装放弃却留下录音笔",
        "cliffhanger_type": "揭露" if ep == 1 else "倒计时",
        "estimated_seconds": 30,
    }


def good_state(ep: int, leak: str | None = None) -> dict:
    return {
        "characters": {
            "lin-wan": {
                "location": "车内", "injured": False, "holds": ["录音笔"],
                "dead": False, "written_out": False,
                "knows": ["顾彦辰出现在车库"],
                "believes": ["他在替别人做事"],
                "suspects": ["他和姐姐的死有关"],
                "must_not_know": ["顾彦辰的真实身份", "存储卡在他口袋里"],
            },
            "gu-yanchen": {"location": "电梯口", "dead": False, "written_out": False,
                           "knows": ["林晚在找卡"], "believes": [], "suspects": [],
                           "must_not_know": ["林晚留了录音笔"]},
        },
        "props": {"dashcam": {"status": "被拿走", "holder": "gu-yanchen"}},
        "open_threads": ["t-01"],
    }


def good_review() -> dict:
    dims = ["hook", "causality", "character_consistency", "voice_distinctness",
            "value_shift", "information_management", "emotional_payoff", "originality"]
    return {
        "round": 1,
        "scores": {d: {"score": 4, "evidence": "原文引用：你早就知道了，对吧？"} for d in dims},
        "issues": [], "verdict": "approved", "total": 32, "threshold": 32,
    }


BASE_SCRIPT = """# 第 1 集

## 场景 1：地下库 · 夜
（林晚、顾彦辰）

【人物】林晚｜个性：信证据不信人，被噎住时反而更安静｜外表：28 岁偏瘦，眼下发青，指节有旧握笔茧｜穿着：男友风旧夹克袖口磨白，背包带勒出一道折痕｜特征：说谎前先摸耳垂，说真话时直视对方

【人物】顾彦辰｜个性：把话绕三圈才说重点，永远留一个退路｜外表：35 岁发际线后退，下颌刮得发青，左手无名指有旧戒痕｜穿着：合身深灰夹克，袖扣一丝不苟，鞋尖擦得发亮｜特征：递东西前先在手里转半圈，笑起来只动嘴角

【场景】时间：深夜 ｜ 地点：小区地下车库 B2 层 ｜ 景别：中近景 ｜ 机位：固定 ｜ 光线：冷白灯管顶光，柔 ｜ 色调：水泥灰、冷白低饱和 ｜ 物件：行车记录仪、录音笔、车库门禁卡 ｜ 风格：写实悬疑质感
灯管嗡嗡响，只有她那辆车顶还积着一层灰。远处电梯口的指示灯是唯一的暖色，水泥地上留着两道新鲜的轮胎印，风从坡道口灌进来，把塑料袋吹到车轮底下。

【节拍 1】林晚走向自己的车，顾彦辰已经站在电梯口。

林晚：（没回头）你来得比我想的早。
顾彦辰：（把玩车钥匙）我怕有人比我更早。

【节拍 2】她发现行车记录仪的存储卡不见了。

林晚：卡呢？
顾彦辰：什么卡？

【节拍 3】她假装放弃，把录音笔留在副驾。

（末尾）电梯门合上的一瞬，她看见他口袋里露出的卡角。
"""


def main() -> int:
    # ---------- 用例 1：干净项目应 0 blocker ----------
    base_project(2)
    episode_shell(1, [good_card(1)], BASE_SCRIPT, good_state(1), good_review())
    episode_shell(2, [good_card(2)], BASE_SCRIPT, good_state(2), good_review())
    code, out = run_validate()
    results.append(("干净项目 exit=0", code == 0, out[-400:]))

    # ---------- 用例 1b：状态看板 ----------
    code, out = run_status()
    results.append(("status exit=0", code == 0, out[-400:]))
    expected = ["故事状态看板", "2 / 2 集已通过", "已回收（按计划）", "## 数据健康"]
    ok = all(k in out for k in expected)
    results.append(("status 关键区块", ok, "" if ok else out[-600:]))

    code, out = run_status("--write")
    status_file = PROJ / "STATUS.md"
    ok = code == 0 and status_file.exists() and "## 逐集进度" in status_file.read_text(encoding="utf-8")
    results.append(("status --write", ok, "" if ok else out[-400:]))

    project_file = PROJ / "PROJECT.md"
    expected_project = ["## 项目目标", "## 计划执行", "## 当前进度", "## 质量与风险", "## 文件导航"]
    ok = (code == 0 and project_file.exists()
          and all(k in project_file.read_text(encoding="utf-8") for k in expected_project))
    results.append(("status --write 同步 PROJECT.md", ok, "" if ok else out[-600:]))

    code, out = run_overview("--write")
    ok = code == 0 and project_file.exists() and "## 项目目标" in project_file.read_text(encoding="utf-8")
    results.append(("overview --write", ok, "" if ok else out[-600:]))

    # 伏笔 status=planted 但 planted_at 晚于最新已写集 → 应提示
    tpath = PROJ / "structure/threads.yaml"
    tdata = yaml.safe_load(tpath.read_text(encoding="utf-8"))
    tdata[0]["planted_at"] = 5
    write(tpath, tdata)
    code, out = run_status()
    ok = "status=planted" in out and "晚于最新已写集" in out
    results.append(("status 伏笔状态失真", ok, "" if ok else out[-600:]))
    tdata[0]["planted_at"] = 1
    write(tpath, tdata)

    # ---------- 用例 2：死人出场 (C1) ----------
    st = good_state(1)
    st["characters"]["gu-yanchen"]["dead"] = True
    write(PROJ / "episodes/e01/state.yaml", st)
    code, out = run_validate("--stage", "cards", "--episode", "2")
    expect("C1", out, True, "死人出场")
    results.append(("C1 exit=1", code == 1, ""))

    # 恢复
    write(PROJ / "episodes/e01/state.yaml", good_state(1))

    # ---------- 用例 3：先回收后埋 (C2) ----------
    write(PROJ / "structure/threads.yaml", [
        {"id": "t-bad", "type": "伏笔", "planted_at": 2, "planned_payoff": 1,
         "status": "planted", "description": "倒序伏笔"},
    ])
    code, out = run_validate("--stage", "structure")
    expect("C2", out, True, "先回收后埋")
    results.append(("C2 exit=1", code == 1, ""))
    write(PROJ / "structure/threads.yaml", [
        {"id": "t-01", "type": "伏笔", "planted_at": 1, "planned_payoff": 2,
         "status": "planted", "description": "存储卡"},
    ])

    # ---------- 用例 4：价值无翻转 (C3) ----------
    episode_shell(1, [good_card(1, value_same=True)], BASE_SCRIPT, good_state(1), good_review())
    code, out = run_validate("--stage", "cards", "--episode", "1")
    expect("C3", out, True, "价值无翻转")
    results.append(("C3 exit=1", code == 1, ""))
    episode_shell(1, [good_card(1)], BASE_SCRIPT, good_state(1), good_review())

    # ---------- 用例 5：信息泄露 (C4) ----------
    leak_script = BASE_SCRIPT + "\n林晚：我知道你是顾彦辰的真实身份。"
    episode_shell(1, [good_card(1)], leak_script, good_state(1), good_review())
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C4", out, True, "信息泄露")
    results.append(("C4 exit=1", code == 1, ""))
    episode_shell(1, [good_card(1)], BASE_SCRIPT, good_state(1), good_review())

    # ---------- 用例 6：相邻悬念重复 (C6) ----------
    h = yaml.safe_load((PROJ / "structure/hooks.yaml").read_text(encoding="utf-8"))
    h[1]["cliffhanger_type"] = h[0]["cliffhanger_type"]  # 都改成"揭露"
    write(PROJ / "structure/hooks.yaml", h)
    code, out = run_validate("--stage", "structure")
    expect("C6", out, True, "相邻悬念重复")
    results.append(("C6 exit=1", code == 1, ""))
    h[1]["cliffhanger_type"] = "倒计时"
    write(PROJ / "structure/hooks.yaml", h)

    # ---------- 用例 7：人物字段缺失 (C7) ----------
    cpath = PROJ / "bible/characters/lin-wan.yaml"
    c = yaml.safe_load(cpath.read_text(encoding="utf-8"))
    del c["fear"]
    c["voice_samples"] = ["只有一句"]
    write(cpath, c)
    code, out = run_validate("--stage", "characters")
    expect("C7", out, True, "人物字段缺失")
    results.append(("C7 exit=1", code == 1, ""))
    write(cpath, yaml.safe_load((SKILL / "templates/character.yaml").read_text(
        encoding="utf-8")) | {  # 恢复为合法卡
        "id": "lin-wan", "name": "林晚", "role": "protagonist",
        "want": "拿到存储卡", "fear": "真相毁掉家人", "secret": "隐瞒通话",
        "lie": "只是查清楚", "wound": "没接电话", "arc": "从逃避到直面",
        "voice_samples": ["a", "b", "c", "d", "e"], "voice_rules": ["短句"],
        "never_say": ["x", "y"], "visible_from": 1, "version": 1,
    })

    # ---------- 用例 8：关系对称 (C8) ----------
    rels = yaml.safe_load((PROJ / "bible/relations.yaml").read_text(encoding="utf-8"))
    rels[0]["power_diff"] = "势均力敌"
    write(PROJ / "bible/relations.yaml", rels)
    code, out = run_validate("--stage", "relations")
    expect("C8", out, True, "关系对称")
    results.append(("C8 exit=1", code == 1, ""))
    rels[0]["power_diff"] = "顾彦辰占优（信息）"
    write(PROJ / "bible/relations.yaml", rels)

    # ---------- 用例 9：连续性巡检 ----------
    code, out = run_continuity()
    results.append(("continuity 干净 exit=0", code == 0, out[-500:]))
    results.append(("continuity 账本区块",
                    "集末状态账本" in out and "人物位置轨迹" in out and "道具账本" in out,
                    "" if "集末状态账本" in out else out[-500:]))

    # K3 价值断链
    hp = PROJ / "structure/hooks.yaml"
    hooks = yaml.safe_load(hp.read_text(encoding="utf-8"))
    hooks[1]["value_before"] = "信任"
    write(hp, hooks)
    code, out = run_continuity()
    expect("K3", out, True, "连续性价值断链")
    results.append(("K3 exit=1", code == 1, ""))
    hooks[1]["value_before"] = "怀疑"
    write(hp, hooks)

    # K4 伏笔提前挂账
    tp = PROJ / "structure/threads.yaml"
    threads = yaml.safe_load(tp.read_text(encoding="utf-8"))
    threads[0]["planted_at"] = 5
    threads[0]["planned_payoff"] = 6
    write(tp, threads)
    code, out = run_continuity()
    expect("K4", out, True, "连续性伏笔提前")
    results.append(("K4 exit=1", code == 1, ""))
    threads[0]["planted_at"] = 1
    threads[0]["planned_payoff"] = 2
    write(tp, threads)

    # K6 道具断链（警告，不阻断）
    s2 = good_state(2)
    s2["props"] = {}
    write(PROJ / "episodes/e02/state.yaml", s2)
    code, out = run_continuity()
    expect("K6", out, True, "连续性道具断链")
    results.append(("K6 exit=0", code == 0, ""))
    write(PROJ / "episodes/e02/state.yaml", good_state(2))

    # K1 有剧本缺 state
    (PROJ / "episodes/e02/state.yaml").unlink()
    code, out = run_continuity()
    expect("K1", out, True, "连续性缺 state")
    results.append(("K1 exit=1", code == 1, ""))
    write(PROJ / "episodes/e02/state.yaml", good_state(2))

    # ---------- 用例 10：场景与人物描述 QC（C10 / C11） ----------
    c10c = PROJ / "episodes/e01/cards.yaml"
    s10c = PROJ / "episodes/e01/script.md"

    def mutate_card(field, broken):
        """把 e01 第一张卡的 field 换成 broken（None=删字段），返回原值。"""
        data = yaml.safe_load(c10c.read_text(encoding="utf-8"))
        old = data[0].pop(field, None)
        if broken is not None:
            data[0][field] = broken
        write(c10c, data)
        return old

    def restore_card(field, old):
        data = yaml.safe_load(c10c.read_text(encoding="utf-8"))
        data[0][field] = old
        write(c10c, data)

    # 场景卡：缺描述 / 描述过短 / 缺道具 / 缺视觉节拍
    for label, rule, field, broken in [
        ("缺 scene_description", "C10-card-scene", "scene_description", None),
        ("scene_description 过短", "C10-card-scene", "scene_description", "太短"),
        ("缺 props", "C10-card-props", "props", None),
        ("visual_beats 不足", "C10-card-beats", "visual_beats", ["只有一条"]),
    ]:
        old = mutate_card(field, broken)
        code, out = run_validate("--stage", "cards", "--episode", "1")
        expect(rule, out, True, label)
        results.append((f"{rule}·{label} exit=1", code == 1, ""))
        restore_card(field, old)

    # C10 v2：锚点引用 / 景别机位枚举 / 光线质感 / 色板漂移 / 模糊词
    for label, rule, field, broken in [
        ("缺 scene_ref", "C10-card-ref", "scene_ref", None),
        ("scene_ref 不存在", "C10-card-ref", "scene_ref", "no-such-anchor"),
        ("scene_ref 挂错锚点", "C10-card-ref", "scene_ref", "market-gate"),
        ("shot_size 缺枚举", "C10-card-shot", "shot_size", None),
        ("shot_size 非法值", "C10-card-shot", "shot_size", "大特写"),
        ("camera 非法值", "C10-card-shot", "camera", "旋转"),
        ("lighting 缺失", "C10-card-light", "lighting", None),
        ("lighting 不含光", "C10-card-light", "lighting", "右侧暖意，柔柔的"),
        ("lighting 缺软硬", "C10-card-light", "lighting", "右侧暖光照进来"),
        ("palette 缺锚点固定色", "C10-card-palette", "palette", "暖黄、促销红"),
        ("scene_description 模糊词", "C10-fuzzy", "scene_description",
         "深夜的地下车库很有氛围感，一切都那么唯美，仿佛时间静止了一般，冷白灯管在头顶嗡嗡作响。"),
    ]:
        old = mutate_card(field, broken)
        code, out = run_validate("--stage", "cards", "--episode", "1")
        expect(rule, out, True, label)
        results.append((f"{rule}·{label} exit=1", code == 1, out[-300:]))
        restore_card(field, old)

    # 人物卡：缺形象四件套
    for field in ["persona", "appearance", "wardrobe", "signature"]:
        cp = PROJ / "bible/characters/lin-wan.yaml"
        data = yaml.safe_load(cp.read_text(encoding="utf-8"))
        old = data.pop(field)
        write(cp, data)
        code, out = run_validate("--stage", "characters")
        expect("C11-card-persona", out, True, f"人物卡缺 {field}")
        results.append((f"C11-card·{field} exit=1", code == 1, ""))
        data[field] = old
        write(cp, data)

    # 剧本：缺【场景】行 / 缺要素 / 描述过短
    base_script = s10c.read_text(encoding="utf-8")

    def mutate_script(broken: str):
        s10c.write_text(broken, encoding="utf-8")

    scene_block = re.search(r"【场景】[^\n]*\n[^\n]*\n", base_script).group(0)
    mutate_script(base_script.replace(scene_block, ""))
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C10-script-scene", out, True, "剧本缺【场景】行")
    results.append(("C10-script-scene exit=1", code == 1, ""))

    mutate_script(re.sub(r" *｜ *风格：[^｜\n]*", "", base_script, count=1))
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C10-script-scene-tags", out, True, "【场景】缺风格")
    results.append(("C10-script-scene-tags exit=1", code == 1, out))

    short_scene = ("【场景】时间：深夜 ｜ 地点：地下车库 ｜ 景别：中近景 ｜ 机位：固定 ｜ "
                   "光线：冷白灯管顶光，柔 ｜ 色调：水泥灰、冷白 ｜ 物件：录音笔 ｜ 风格：写实\n太短。\n\n")
    mutate_script(base_script.replace(scene_block, short_scene))
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C10-script-scene-body", out, True, "场景描述过短")
    results.append(("C10-script-scene-body exit=1", code == 1, ""))

    # C10 v2 剧本侧：缺镜头标签 / 枚举违规 / 光线质感 / 色调过短 / 模糊词
    for label, rule, mutate in [
        ("【场景】缺景别", "C10-script-scene-tags",
         lambda s: re.sub(r" *｜ *景别：[^｜\n]*", "", s, count=1)),
        ("景别非法值", "C10-script-shot",
         lambda s: s.replace("景别：中近景", "景别：大特写", 1)),
        ("机位非法值", "C10-script-shot",
         lambda s: s.replace("机位：固定", "机位：旋转", 1)),
        ("光线缺软硬词", "C10-script-light",
         lambda s: s.replace("光线：冷白灯管顶光，柔", "光线：冷白灯管顶光", 1)),
        ("色调过短", "C10-script-palette",
         lambda s: s.replace("色调：水泥灰、冷白低饱和", "色调：灰", 1)),
        ("描述段模糊词", "C10-fuzzy", None),
    ]:
        if mutate is None:
            bad_body = scene_block.replace(
                scene_block.split("\n")[1],
                scene_block.split("\n")[1] + "灯光下的一切都很有氛围感，唯美得仿佛电影画面。")
            mutate_script(base_script.replace(scene_block, bad_body))
        else:
            mutate_script(mutate(base_script))
        code, out = run_validate("--stage", "script", "--episode", "1")
        expect(rule, out, True, label)
        results.append((f"{rule}·{label} exit=1", code == 1, out[-300:]))

    # 剧本：缺【人物】行 / 缺要素
    mutate_script(re.sub(r"【人物】林晚[^\n]*\n", "", base_script))
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C11-script-persona", out, True, "首次出场缺【人物】行")
    results.append(("C11-script-persona exit=1", code == 1, ""))

    mutate_script(base_script.replace("｜穿着：男友风旧夹克袖口磨白，背包带勒出一道折痕", ""))
    code, out = run_validate("--stage", "script", "--episode", "1")
    expect("C11-script-persona-tags", out, True, "【人物】缺穿着")
    results.append(("C11-script-persona-tags exit=1", code == 1, ""))

    # 描述块不计入表演时长（塞进超长【场景】描述，估算秒数必须不变）
    _, clean_out = run_validate("--stage", "script", "--episode", "1")
    clean_sec = (re.search(r"预估时长 (\d+)s", clean_out) or [None, None])[1]
    pad = ("【场景】时间：深夜 ｜ 地点：地下车库 ｜ 景别：中近景 ｜ 机位：固定 ｜ "
           "光线：冷白灯管顶光，柔 ｜ 色调：水泥灰、冷白 ｜ 物件：录音笔 ｜ 风格：写实\n"
           + ("灯管嗡嗡响，水泥地反着冷光，回声比人声晚半拍。" * 15) + "\n\n")
    mutate_script(base_script.replace(scene_block, scene_block + "\n" + pad))
    code, out = run_validate("--stage", "script", "--episode", "1")
    pad_sec = (re.search(r"预估时长 (\d+)s", out) or [None, None])[1]
    results.append(("描述块不计时长（秒数不变）",
                    code == 0 and clean_sec is not None and pad_sec == clean_sec,
                    f"clean={clean_sec} pad={pad_sec}\n{out}"))

    # 在场行（谁在场）也是说明，不计入表演时长：加长在场行秒数必须不变
    m_cast = re.search(r"(?m)^## 场景 [^\n]*\n（[^\n]*）", base_script)
    long_cast = m_cast.group(0)[:-1] + "、群演甲、群演乙、群演丙）"
    mutate_script(base_script.replace(m_cast.group(0), long_cast))
    code, out = run_validate("--stage", "script", "--episode", "1")
    cast_sec = (re.search(r"预估时长 (\d+)s", out) or [None, None])[1]
    results.append(("在场行不计时长（秒数不变）",
                    code == 0 and clean_sec is not None and cast_sec == clean_sec,
                    f"clean={clean_sec} cast={cast_sec}\n{out}"))
    s10c.write_text(base_script, encoding="utf-8")

    # 恢复后整包必须全绿
    code, out = run_validate()
    results.append(("QC 用例后全绿 exit=0", code == 0, out[-500:]))

    # ---------- 清理 ----------
    shutil.rmtree(PROJ, ignore_errors=True)

    # 汇总
    failed = [r for r in results if not r[1]]
    for name, ok, detail in results:
        print(f"  {'✅' if ok else '❌'} {name}" + (f"  {detail}" if detail and not ok else ""))
    print(f"\n{len(results) - len(failed)}/{len(results)} 通过")
    if failed:
        print("存在回归，修复后再提交 skill 修改。")
        return 1
    print("全绿 — skill 修改安全。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
