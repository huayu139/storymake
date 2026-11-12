#!/usr/bin/env python3
"""场景提示词导出器：把场景卡 + 场景锚点 + 人物形象拼成可直接粘贴的
生图 / 生视频提示词（调研结论见 docs/scene-prompt-design.md 第 2.4 节）。

用法:
    prompt.py <slug> --episode N [--scene K] [--mode image|video] [--write]

- 默认输出 image（文生图）提示词；--mode video 追加动作节拍、声音与单镜约束。
- --scene K 只导出第 K 场（1 起）；缺省导出该集全部场。
- --write 额外写入 episodes/eNN/prompts.md，终端仍打印。

拼装顺序（靠前权重高，按各家官方公式收敛）:
    [主体] 人物形象四件套 + [场景] 锚点空间基因 + 色板/光线 + [镜头] 景别机位竖屏
    + [动作] visual_beats + [风格] 风格标签 + [约束] 保持项 + [负向] 负向词

红线: must_not_happen / must_not_know / hidden 是创作边界，结构性排除，
      永不进入提示词（C4 面向人读，本脚本负责机器侧不漏）。

退出码: 0 = 导出完成；1 = 用法/项目错误。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# 本脚本位于 .opencode/skill/story-workbench/scripts/prompt.py
ROOT = Path(__file__).resolve().parents[4]

# 固定负向词（可观察原则的反面：模糊词、畸形、乱码文字一律不要）
NEGATIVE = (
    "模糊词堆砌，氛围感，高级感，唯美，电影感，畸形，多余手指，"
    "多余肢体，扭曲面部，乱码文字，水印，logo，字幕，低质量，过曝"
)

# 保持项：跨镜头一致性约束（正面表达，不写"不要"以外的否定指令）
KEEP = (
    "保持人物五官与服装与参考一致，不新增画面人物，画面内不出现文字与字幕，"
    "竖屏构图，主体居中偏上，背景纵深可见"
)


# ---------------------------------------------------------------- 基础工具
def read_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — 解析失败交由调用方按缺失处理
        return None


def load_scenes(proj: Path) -> dict[str, dict]:
    data = read_yaml(proj / "bible/scenes.yaml")
    out: dict[str, dict] = {}
    if isinstance(data, dict):
        for s in data.get("scenes") or []:
            if isinstance(s, dict) and s.get("id"):
                out[str(s["id"])] = s
    return out


def load_chars(proj: Path) -> dict[str, dict]:
    """人物形象四件套：persona/appearance/wardrobe/signature。"""
    out: dict[str, dict] = {}
    d = proj / "bible/characters"
    if not d.exists():
        return out
    for f in sorted(d.glob("*.yaml")):
        data = read_yaml(f)
        if isinstance(data, dict) and data.get("id"):
            out[str(data["id"])] = data
    return out


def parse_script_scenes(text: str) -> list[dict]:
    """按 '## 场景 N：' 切剧本，取每场的风格标签与对白原句。"""
    parts = re.split(r"^(## 场景 \d+[^\n]*)$", text, flags=re.M)
    out: list[dict] = []
    for i in range(1, len(parts), 2):
        head, body = parts[i], parts[i + 1]
        style = ""
        m = re.search(r"｜ *风格：([^｜\n]*)", head + body)
        if m:
            style = m.group(1).strip()
        # 对白行：形如「名字：台词」（不含【】与括号说明行）
        lines = [ln.strip() for ln in body.splitlines()
                 if re.match(r"^[^【（(【\s][^：]{1,8}：", ln.strip())]
        out.append({"head": head.strip(), "style": style, "lines": lines})
    return out


# ---------------------------------------------------------------- 拼装
def subject_block(cast: list[str], chars: dict[str, dict]) -> str:
    """[主体] 人物形象四件套（同一角色跨镜头复用同一段，防漂移）。"""
    parts = []
    for cid in cast:
        ch = chars.get(cid)
        if not ch:
            parts.append(f"- {cid}（无形象四件套，先补人物卡）")
            continue
        parts.append(
            f"- {ch.get('name', cid)}：{ch.get('appearance', '')}；"
            f"穿着 {ch.get('wardrobe', '')}；习惯动作 {ch.get('signature', '')}"
        )
    return "\n".join(parts) if parts else "- （本场无 cast）"


def scene_block(card: dict, anchor: dict | None) -> str:
    """[场景] 锚点空间基因在前，本场色板/光线差异在后。"""
    if not anchor:
        return f"场景：{card.get('location', '')}（无锚点，仅本场描述）"
    palette = str(card.get("palette") or "")
    core = "、".join(str(x) for x in (anchor.get("palette_core") or []))
    return (
        f"空间：{anchor.get('space', '')}\n"
        f"固定色板：{core}；本场色调：{palette}\n"
        f"光线：{card.get('lighting', '')}（基调 {anchor.get('lighting_anchor', '')}）\n"
        f"环境音参考：{anchor.get('ambience', '')}"
    )


def build_prompt(card: dict, anchor: dict | None, chars: dict[str, dict],
                 style: str, mode: str) -> str:
    """按官方公式顺序拼一条完整提示词。"""
    sid = card.get("scene_id", "?")
    lines: list[str] = []
    lines.append(f"### {sid} · {card.get('location', '')}（{card.get('time', '')}）")
    lines.append("")
    lines.append("[主体]")
    lines.append(subject_block([str(c) for c in (card.get("cast") or [])], chars))
    lines.append("")
    lines.append("[场景]")
    lines.append(scene_block(card, anchor))
    lines.append("")
    lines.append("[镜头]")
    lines.append(
        f"{card.get('shot_size', '')}，机位：{card.get('camera', '')}，"
        f"9:16 竖屏，{anchor.get('vertical', '') if anchor else '主体居中'}"
    )
    lines.append("")
    if mode == "video":
        beats = [str(b) for b in (card.get("visual_beats") or [])]
        lines.append("[动作]（一镜一动作，按节拍分段生成）")
        lines.extend(f"- {b}" for b in beats)
        lines.append("")
        lines.append("[声音]（音画同步）")
        amb = anchor.get("ambience", "") if anchor else ""
        lines.append(f"环境音：{amb}；对白见剧本原句，无背景音乐")
        lines.append("")
    lines.append("[风格]")
    lines.append(style or "写实纪录质感")
    lines.append("")
    lines.append("[约束/保持项]")
    lines.append(KEEP)
    lines.append("")
    lines.append("[负向词]")
    lines.append(NEGATIVE)
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="场景提示词导出器")
    ap.add_argument("slug", help="项目目录名 projects/<slug>")
    ap.add_argument("--episode", type=int, required=True, help="集号（1 起）")
    ap.add_argument("--scene", type=int, default=None, help="只导出第 K 场（1 起）")
    ap.add_argument("--mode", choices=["image", "video"], default="image")
    ap.add_argument("--write", action="store_true", help="写入 episodes/eNN/prompts.md")
    args = ap.parse_args(argv)

    proj = ROOT / "projects" / args.slug
    if not proj.exists():
        print(f"项目不存在: {proj}", file=sys.stderr)
        return 1

    cards_path = proj / f"episodes/e{args.episode:02d}/cards.yaml"
    cards = read_yaml(cards_path)
    if not isinstance(cards, list) or not cards:
        print(f"场景卡缺失或为空: {cards_path}", file=sys.stderr)
        return 1

    script_path = proj / f"episodes/e{args.episode:02d}/script.md"
    script_scenes = parse_script_scenes(
        script_path.read_text(encoding="utf-8") if script_path.exists() else "")

    scenes = load_scenes(proj)
    chars = load_chars(proj)

    blocks = []
    for idx, card in enumerate(cards):
        if args.scene is not None and not str(card.get("scene_id", "")).endswith(
                f"-sc{args.scene:02d}"):
            continue
        ref = str(card.get("scene_ref") or "")
        anchor = scenes.get(ref)
        style = script_scenes[idx]["style"] if idx < len(script_scenes) else ""
        blocks.append(build_prompt(card, anchor, chars, style, args.mode))

    if not blocks:
        print(f"未找到第 {args.scene} 场", file=sys.stderr)
        return 1

    title = (f"# 第 {args.episode} 集提示词（{args.mode}）\n\n"
             f"> 由 prompt.py 从场景卡 + bible/scenes.yaml 自动拼装；"
             f"锚点复用保证跨集一致。红线字段（禁写项与隐藏信息）已结构性排除。\n\n")
    out = title + "\n\n---\n\n".join(blocks) + "\n"
    print(out)

    if args.write:
        dest = script_path.parent / "prompts.md"
        dest.write_text(out, encoding="utf-8")
        print(f"已写入 {dest}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
