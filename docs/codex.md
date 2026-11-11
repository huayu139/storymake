# 在 Codex 中使用 Story Lab

> 适用：Codex CLI、Codex IDE 扩展、ChatGPT 桌面端的 Codex，以及 Codex Cloud。
> 本项目同时支持 OpenCode 与 Codex：同一套 `SKILL.md` + 脚本，用目录软链桥接两边的发现规则。

---

## 1. 原理

Codex 使用 **Agent Skills** 标准，扫描位置包括：

- `$CWD/.agents/skills`
- 仓库根目录的 `.agents/skills`
- `$HOME/.agents/skills`
- `/etc/codex/skills`

本项目已建立仓库级软链：

```text
.agents/skills/story-workbench
  -> ../../.opencode/skill/story-workbench
```

因此 Codex 能发现 `SKILL.md`，而脚本仍然只有一份，OpenCode 与 Codex 不会各改一套。

`SKILL.md` 已带 Codex 需要的 frontmatter：

```yaml
---
name: story-workbench
description: 长连载故事创作工作台。当用户要创作/开发短剧……
---
```

---

## 2. 前置检查

```bash
cd /workspace/storymake
ls -la .agents/skills/story-workbench/SKILL.md
/workspace/tools/miniconda3/bin/python -c "import yaml; print(yaml.__version__)"
codex --version
```

期望：

- 软链可读；
- PyYAML 可用（当前在 Miniconda 里，版本 6.x）；
- Codex 已安装。

如果 Codex 未安装，按其官方方式安装后执行 `codex`。本机目前没有 `codex` 命令，需先安装或在另一台机器上使用。

---

## 3. 启动与确认

```bash
cd /workspace/storymake
codex
```

进入 Codex 后：

```text
/skills
```

应能看到 `story-workbench`。也可以直接用 `$` 显式调用：

```text
$story-workbench 读取当前项目，运行 status.py，告诉我进度和下一步
```

Codex 也支持隐式触发：当你说“继续写第 11 集”“看一下伏笔”“评审这一集”等，且任务与 description 匹配时，可能自动加载该技能。为避免误触发，建议重要操作显式写 `$story-workbench`。

---

## 4. 常用指令

```text
$story-workbench 现在做到哪了？先跑 status.py，再解释下一步
```

```text
$story-workbench 继续 e11 的 S5 场景卡，给我 3 个方案，标注各自风险
```

```text
$story-workbench 按用户选定的方案写 e11 的 cards.yaml，写完跑 validate.py
```

```text
$story-workbench 写 e11 剧本，控制在 90 秒 ±20%
```

```text
$story-workbench 用全新上下文的 subagent 评审 e11，按 8 维打分并引用原文
```

```text
$story-workbench 巡检连续性，跑 continuity.py，把 BLOCKER 和 WARN 都列出来
```

```text
$story-workbench 刷新 PROJECT.md 和 STATUS.md
```

```text
$story-workbench 启动 Web 看板，绑定 0.0.0.0:8765
```

Codex CLI 非交互模式也可以：

```bash
codex exec '$story-workbench 读取 projects/urban-counterattack，汇报当前进度和下一步'
```

---

## 5. Codex 与 OpenCode 的差异

| 项 | OpenCode | Codex |
|---|---|---|
| 技能目录 | `.opencode/skill/` | `.agents/skills/` |
| 显式调用 | 由 harness 自动加载或提及 | `/skills` 或 `$story-workbench` |
| 项目约束 | `AGENTS.md` | `AGENTS.md` |
| 脚本执行 | 直接调用 | 可能触发沙箱/审批 |
| 权限 | 由 OpenCode 控制 | 需信任项目或逐条批准命令 |

桥接方式就是软链。不要在两处分别维护副本。

---

## 6. Codex 沙箱与权限

技能里的命令会调用：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/status.py urban-counterattack
```

Codex 默认可能对以下操作要求确认：

- 读取 `/workspace/tools` 下的 Python；
- 执行项目内脚本；
- 启动监听 8765 的 Web 服务。

建议：

- 在 Codex 中把 `/workspace/storymake` 设为可信工作区；
- 首次运行时允许“执行项目内命令”；
- Web 看板只在需要时启动，避免常驻占用端口。

如果 Codex 在容器里运行且 `/workspace/tools` 不存在，给它一个可用的 Python 3 + PyYAML 即可，然后把命令里的解释器路径换成实际路径。

---

## 7. Codex Cloud

Codex Cloud 从 Git 仓库拉代码，所以需要：

1. 仓库同时包含 `.agents/skills/story-workbench`（软链）与 `.opencode/skill/story-workbench`（真实技能目录）。
2. Git 保留软链。若目标平台不支持软链，改为**复制**整个技能目录到 `.agents/skills/story-workbench`。
3. 云端环境安装 Python 3 与 PyYAML（例如 `pip install pyyaml`），并把命令中的解释器改为 `python3`。
4. 云端没有 `/workspace/tools`，不要照搬本机的绝对路径。

注意：复制到 `.agents/skills/story-workbench` 后，脚本的 `ROOT` 计算仍然正确，因为目录深度与 `.opencode/skill/story-workbench` 相同（都是项目根下 4 层）。**但不要安装到 `$HOME/.agents/skills`**，那会让脚本把家目录误当项目根。

---

## 8. 首次验证清单

```text
1. cd /workspace/storymake && codex
2. /skills 看到 story-workbench
3. $story-workbench 读取 projects/urban-counterattack/PROJECT.md 并汇报进度
4. 确认它先跑 status.py，而不是凭记忆回答
5. 让它跑一次 validate.py urban-counterattack，确认能执行本地脚本
6. 让它打开 http://127.0.0.1:8765，确认 Web 看板可用
```

通过后即可按正常创作流程使用。

---

## 9. 常见问题

| 现象 | 处理 |
|---|---|
| `/skills` 看不到 | 确认在 `/workspace/storymake` 启动；确认软链目标存在；重启 Codex |
| 技能被错误触发 | 用 `$story-workbench` 显式调用；或在代码任务中避免“故事/剧本/分集”等词 |
| 脚本报 `ModuleNotFoundError: yaml` | 换用 `/workspace/tools/miniconda3/bin/python`，或安装 PyYAML |
| `ROOT` 指错目录 | 不要把技能装到 `$HOME/.agents/skills`；保持仓库级安装 |
| Web 端口被占用 | 换 `--port 8766` |
| Codex 反复要权限 | 信任项目，或把常用命令加入允许列表 |
| 云端软链失效 | 改为复制技能目录到 `.agents/skills/story-workbench` |

---

## 10. 维护约定

- 只改 `.opencode/skill/story-workbench/` 下的真实文件；`.agents/skills/story-workbench` 只是软链。
- 改完技能后跑 `evals/run_evals.py`，保持全绿。
- 新增技能时，同样在 `.agents/skills/` 建软链，不要复制两份。
- 本文件与 `AGENTS.md` 的 Codex 小节同步维护。
