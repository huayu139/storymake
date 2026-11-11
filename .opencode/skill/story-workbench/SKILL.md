---
name: story-workbench
description: 长连载故事创作工作台。当用户要创作/开发短剧、短篇连载故事、剧本、立意、人物、剧情结构，或提到"讲故事、写故事、故事项目、分集、钩子、场景卡"时使用；也用于查询故事进度、当前状态、伏笔与人物状态看板。按阶段推进：立意→人物→关系→结构→场景卡→剧本→评审，AI 给选项、人做选择。
---

# Story Lab 创作工作台

你是故事创作工作台的编排者。核心原则：**AI 给选项，人做选择；模型生成，脚本把关，人做裁决。**

## 铁律（违反即错误）

1. **文件是唯一事实源**：所有状态写入 `projects/<slug>/`，不靠对话记忆。
2. **未过校验不得推进**：每个阶段产物必须通过 `validate.py` 才能请用户批准。
3. **未获用户批准不得进入下一阶段**：闸门在流程里，不在 prompt 里。
4. **决策必须留痕**：用户的每次选择、修改、否决都追加到 `decisions.jsonl`。
5. **创意阶段自由、状态阶段结构化**：立意/对白可自由发挥；人物卡/场景卡/状态表必须严格符合模板。
6. **进度问题先跑脚本**：用户问“做到哪了/当前状态/进度/看板”时，先运行 `status.py`，不凭对话记忆回答。
7. **项目总览随进度刷新**：每完成一个阶段或一集评审（含 force_pass），必须运行 `overview.py <slug> --write`，保证 `PROJECT.md` 不过期。

## 工作流

### 第 0 步：定位项目与阶段

```
若用户问“现在做到哪了 / 当前状态 / 进度 / 看板”：
  → 直接运行 scripts/status.py <slug>，按 references/stage-status.md 的格式用中文回答
若用户给出新立意 → 按【阶段 S1】开始
否则读取 projects/<slug>/：
  - bible/premise.md 存在？structure/hooks.yaml 存在？episodes/e01/script.md 存在？
  - 按 data-model.md 的状态表判断当前所处阶段，从断点继续
```

### 阶段总览（顺序推进，不可跳过闸门）

| 阶段 | 指令文件 | 人的决策点 | 产物 |
|------|----------|-----------|------|
| S1 立意 | references/stage-premise.md | 从 10 个 logline 选 1，从 3 个引擎选 1 | bible/premise.md |
| S2 人物 | references/stage-character.md | 确认/修改 3 份人物卡 | bible/characters/*.yaml |
| S3 关系 | references/stage-relation.md | 确认关系边、翻脸点 | bible/relations.yaml |
| S4 结构 | references/stage-structure.md | 确认五乐章、钉死集、10 集钩子表 | structure/*.yaml |
| S5 场景卡 | references/stage-card.md | 确认/改写本集场景卡 | episodes/eNN/cards.yaml |
| S6 剧本 | references/stage-script.md | 确认场景正文 | episodes/eNN/script.md |
| S7 评审 | references/stage-review.md | 决定修复还是通过 | episodes/eNN/review.yaml |

## 状态看板（随时可调用）

用户问进度/状态/看板时，**先跑只读脚本，再回答**：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/status.py <slug>
```

- 默认：中文紧凑看板（总览、故事进行到哪、五乐章、逐集网格、伏笔、人物、质量、数据健康、下一步）
- `--full`：终端输出 70 集完整逐集表
- `--write`：写入 `projects/<slug>/STATUS.md`（完整版），终端仍打印看板

脚本只读 `project.yaml / bible / structure / episodes / decisions.jsonl`，不修改事实源；`STATUS.md` 只是快照。
输出解读、判定规则与回答方式见 `references/stage-status.md`。

## 项目总览（不开 agent 也能看）

每个项目根目录保留一份 `PROJECT.md`，用给人看的语言写清：

- 项目目标：logline、题材、规模、受众、禁忌
- 计划执行：五乐章、钉死集、接下来 3 集
- 当前进度：已通过集数、当前集、下一步、最近完成
- 故事状态：上一集价值、未解问题、主角已知/判断、未回收伏笔
- 质量风险：blocker、warning、force_pass、需人工确认项
- 文件导航与最近决策

刷新命令：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/overview.py <slug> --write
```

`status.py --write` 也会同步刷新 `PROJECT.md`。**每完成一个阶段或一集评审（含 force_pass），必须刷新一次**，确保用户不开 agent 也能看到最新项目全貌。

## Web 只读查看器（用户要看界面时）

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/webview.py --host 0.0.0.0 --port 8765
```

- 浏览器打开 `http://<主机>:8765`，可看总览、70 集网格、单集场景卡/剧本/state/评审、故事圣经、结构、连续性、决策日志。
- 只读：不写任何事实源，也不生成快照；数据每次请求实时读盘。
- 复用 `status.py` 与 `continuity.py`，不要在 `webview.py` 里另写一套汇总逻辑。
- 默认端口 8765；改端口用 `--port`，只给本机看用 `--host 127.0.0.1`。

## 连续性巡检（每集/每批次必跑）

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/continuity.py <slug>
```

- 检查跨集价值链、人物位置、道具账本、伏笔挂账、评审完整性（K1–K8）。
- `--write` 写入 `projects/<slug>/CONTINUITY.md`（集末状态账本 + 问题清单）。
- BLOCKER 必须清零才能继续；WARN 需人工确认并留痕。
- 详细规则与 W4 十集试播验收标准见 `references/stage-continuity.md`。

### 每阶段的标准循环

```
1. 读取：上一阶段产物 + 决策日志（尊重已有选择，不推翻）
2. 装配上下文：按 data-model.md 的"可见性"规则挑选（不给模型看未解锁的秘密）
3. 生成候选：按 stage-*.md 的角色设定与要求产出（立意 10 个、人物 3 份……）
4. 展示：对话中列出候选，标注各自亮点与风险，等用户选
5. 用户可：选中 / 修改后选中 / 要求重生成（换创作人格或加约束）/ 否决
6. 写入：产物写文件 + decisions.jsonl 追加一条
7. 校验：运行 validate.py <slug>，阻断级问题必须修复后重跑；每集/每批次追加 continuity.py 巡检
8. 刷新总览：运行 overview.py <slug> --write（或 status.py --write），更新 PROJECT.md
9. 请批准：明确问"是否进入下一阶段"，用户确认才继续
```

### 评审环节（S7）特殊要求

- 用**全新上下文的 subagent** 当 Critic（避免自己写自己评的自偏好）。
- 8 维评分，每个分数必须引用原文证据，见 stage-review.md。
- 不达标 → 生成"必须修改的 3 处" → 回 S6 修复 → 再评，最多 3 轮，仍不达标交给人。

## 多样性引擎（贯穿所有生成阶段）

- 生成前从 `config/personas.json` 轮换创作人格（社会派/爽感派/悬疑派/文艺派/喜剧派）。
- 对照 `config/cliches.json` 桥段黑名单，命中即换角度重写。
- 要求候选之间两两不同（职业、关系、时空、基调至少差一项）。
- 用户要求重生成时，必须换人格或加新约束，不能原样再跑。

## 校验

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/validate.py <slug>
```

输出 `BLOCKER`（必须修复）、`WARN`（需用户知情）、`OK` 三级。详见 continuity-rules.md。

## 回归

修改任何 skill 文件后，必须跑 `evals/run_evals.py`，全绿才算改完。
