# Story Lab · 长连载故事创作工作台

一个**本地优先、文件为源、AI 给选项、人做选择**的长连载故事创作工作台。

以 Agent Skill 承载创作编排，以确定性 Python 脚本承载校验，以 Markdown / YAML 文件承载记忆。适用于短剧、短篇连载、分集剧本等需要长期连载与跨集一致性的创作。

> 本仓库只包含**工作台/系统本身**，不包含任何具体故事项目。使用前请自备或新建 `projects/<slug>/`。

---

## 特点

- **AI 给选项，人做选择**：每个阶段给候选，用户选中/修改/否决，agent 不替用户拍板。
- **文件即事实源**：所有状态可从磁盘重建，不依赖对话记忆。
- **确定性硬闸门**：价值翻转、连续性、schema、伏笔时序由脚本校验，模型自查不算数。
- **七阶段工作流**：立意 → 人物 → 关系 → 结构 → 场景卡 → 剧本 → 评审。
- **跨集对账**：人物位置、道具、伏笔、价值线逐集巡检。
- **只读 Web 看板**：零依赖前端，实时读取项目文件。
- **双端可用**：同一套技能同时支持 OpenCode 与 Codex。

---

## 环境要求

- Python **3.10+**
- [PyYAML](https://pypi.org/project/PyYAML/)

```bash
python3 -m pip install pyyaml
```

---

## 快速开始

```bash
git clone https://github.com/<OWNER>/<REPO>.git
cd <REPO>

# 1. 安装依赖
python3 -m pip install pyyaml

# 2. 新建一个故事项目目录
mkdir -p projects/my-story

# 3. 在 OpenCode / Codex 中让 skill 从 S1 开始创建项目
```

也可以直接运行只读脚本（需要已有项目）：

```bash
# 进度看板
python3 .opencode/skill/story-workbench/scripts/status.py my-story

# 硬闸门校验
python3 .opencode/skill/story-workbench/scripts/validate.py my-story

# 跨集连续性巡检
python3 .opencode/skill/story-workbench/scripts/continuity.py my-story

# 生成项目总览
python3 .opencode/skill/story-workbench/scripts/overview.py my-story --write

# 启动只读 Web 看板
python3 .opencode/skill/story-workbench/scripts/webview.py --host 127.0.0.1 --port 8765
```

---

## 目录结构

```text
.
├── .opencode/skill/story-workbench/   # 工作台本体
│   ├── SKILL.md                       # 主工作流与闸门
│   ├── references/                    # 阶段说明与规则
│   ├── templates/                     # YAML 模板
│   ├── config/                        # 桥段黑名单、创作人格
│   ├── scripts/                       # 校验、看板、巡检、Web 服务
│   └── web/                           # 零依赖前端
├── .agents/skills/story-workbench     # Codex 软链
├── docs/                              # 架构、交付件、Codex 说明
├── evals/                             # 回归测试
├── projects/                          # 故事项目（本地，不进仓库）
├── AGENTS.md                          # 项目约束
├── PLAN.md                            # 计划与里程碑
└── opencode.example.json              # OpenCode 配置示例
```

故事项目的标准结构：

```text
projects/<slug>/
├── project.yaml
├── decisions.jsonl
├── bible/
├── structure/
├── episodes/eNN/{cards,script,state,review}
├── PROJECT.md            # 快照
├── STATUS.md             # 快照
└── CONTINUITY.md         # 快照
```

> 仓库只保留一个空的 `projects/` 目录（通过 0 字节的 `projects/.gitkeep` 占位），
> `projects/` 下的任何故事内容都会被 `.gitignore` 排除，不会上传到 GitHub。

---

## 在 OpenCode 中使用

本仓库的 `.opencode/skill/story-workbench/` 会被 OpenCode 自动发现。

```text
@story-workbench 现在做到哪了？
@story-workbench 继续 e11，给我 3 个场景卡方案
@story-workbench 写 e11 剧本，控制在 90 秒 ±20%
@story-workbench 评审 e11，用全新上下文的 subagent
```

---

## 在 Codex 中使用

仓库已提供软链：

```text
.agents/skills/story-workbench -> ../../.opencode/skill/story-workbench
```

在 Codex 中：

```text
/skills                  # 确认能看到 story-workbench
$story-workbench 读取当前项目，汇报进度和下一步
```

Codex Cloud 或 Windows 不支持软链时，把 `.opencode/skill/story-workbench/` 复制为 `.agents/skills/story-workbench/` 即可。不要把技能安装到 `$HOME/.agents/skills`，否则脚本会把家目录误当项目根。

详见 [`docs/codex.md`](docs/codex.md)。

---

## 工作流

| 阶段 | 内容 | 人的决策点 | 产物 |
|---|---|---|---|
| S1 立意 | Premise Lab | 从候选 logline / 引擎中选 | `bible/premise.md` |
| S2 人物 | Character Room | 确认/修改人物卡 | `bible/characters/*.yaml` |
| S3 关系 | Relationship Web | 确认关系边与翻脸点 | `bible/relations.yaml` |
| S4 结构 | Story Grid | 确认五乐章、钉死集、钩子表 | `structure/*.yaml` |
| S5 场景卡 | Scene Forge | 确认/改写本集场景卡 | `episodes/eNN/cards.yaml` |
| S6 剧本 | Director-Actor | 确认场景正文 | `episodes/eNN/script.md` |
| S7 评审 | Critic | 修复或通过 | `episodes/eNN/review.yaml` |

标准循环：

```text
读取上阶段产物 + 决策日志
  → 按可见性装配上下文
  → 生成候选
  → 人选择/修改/重生成
  → 写产物 + 追加 decisions.jsonl
  → validate.py（BLOCKER 必须清零）
  → continuity.py（每集/每批次）
  → overview.py --write（刷新 PROJECT.md）
  → 人批准 → 下一阶段
```

---

## 脚本一览

| 脚本 | 作用 |
|---|---|
| `validate.py` | 单阶段/单集硬闸门（C1–C8、W1–W7） |
| `status.py` | 全季进度、伏笔、人物、评审看板 |
| `continuity.py` | 跨集连续性巡检（K1–K8） |
| `overview.py` | 生成面向人的 `PROJECT.md` |
| `webview.py` | 只读 Web 服务与 JSON API |

脚本只读事实源，不修改 `bible/structure/episodes`。`STATUS.md`、`PROJECT.md`、`CONTINUITY.md` 都是可再生成的快照。

---

## 回归测试

修改任何 skill 文件后必须运行：

```bash
python3 evals/run_evals.py
```

测试会在 `projects/__eval_trap__/` 下构造带陷阱的产物，断言校验器能检出每类违规，结束后自动清理。

---

## 仓库不包含什么

- `projects/**`：具体故事内容与分集产物（已在 `.gitignore` 中排除）
- `opencode.json`：本地模型配置，可能含密钥；请用 `opencode.example.json` 自行创建
- `exports/**`：导出产物
- 成片、分镜图、发布包：本工作台只产出文本与结构化创作资产

---

## 迁移与凭证（.keys）

项目的 Git 推送凭证放在 `.keys/`（私钥 + 公钥 + 路径自适应的 `git-ssh.sh`），随整个项目目录一起迁移，不依赖 `~/.ssh` 与 `HOME`。

- `.keys/` 已被 `.gitignore` 排除，**永不进入 Git**；GitHub 上只登记公钥（Deploy key，需 Allow write access）。
- 推送：

```bash
scripts/push.sh
# 或
GIT_SSH_COMMAND="$PWD/.keys/git-ssh.sh" git push
```

- 迁移到新机器用整目录复制（`rsync` / `tar` / `scp`）；只做 `git clone` 不会带上 `.keys/`。
- `.keys/` 丢失时重新生成：`ssh-keygen -t ed25519 -N '' -C storymake-deploy -f .keys/id_ed25519_storymake`，再到仓库 Settings → Keys 登记公钥。

详见 [.keys/README.md](.keys/README.md)。

## 文档

- [`docs/architecture.md`](docs/architecture.md)：分层、铁律、数据流
- [`docs/deliverables.md`](docs/deliverables.md)：交付件清单与外部系统集成
- [`docs/codex.md`](docs/codex.md)：在 Codex 中使用本工作台
- [`.opencode/skill/story-workbench/references/data-model.md`](.opencode/skill/story-workbench/references/data-model.md)：字段与 schema

---

## 许可证

[MIT](LICENSE)
