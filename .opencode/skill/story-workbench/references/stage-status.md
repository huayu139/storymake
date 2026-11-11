# 状态看板（S-Status）

## 何时使用

用户说出以下任意一类话时，**先跑 `status.py`，再回答**：

- “现在做到哪了 / 当前状态 / 进度如何”
- “有没有状态看板 / 看板 / 总览 / 全季进度”
- “还剩多少集 / 下一集是什么 / 哪些集没写”
- “伏笔埋了哪些 / 人物现在什么状态 / 评审过了几集”

不要凭对话记忆回答进度；文件才是事实源。

## 命令

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/status.py <slug>
```

常用参数：

| 参数 | 作用 |
|------|------|
| 无参数 | 终端紧凑看板：总览 + 故事进行到哪 + 五乐章 + 进度网格 + 当前窗口 + 伏笔 + 人物 + 质量 + 数据健康 + 下一步 |
| `--full` | 终端额外输出 70 集完整逐集表 |
| `--write` | 写入 `projects/<slug>/STATUS.md`（完整 70 集版）与 `PROJECT.md`（项目总览），终端仍打印看板 |

示例：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/status.py urban-counterattack

# 生成/刷新完整看板文件
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/status.py urban-counterattack --write
```

## 脚本读什么

只读，不写事实源：

- `project.yaml`：剧名、题材、集数、单集时长
- `bible/premise.md`、`world.md`、`voice.md`、`characters/*.yaml`、`relations.yaml`
- `structure/movements.yaml`、`hooks.yaml`、`threads.yaml`
- `episodes/eNN/{cards.yaml,script.md,state.yaml,review.yaml}`
- `decisions.jsonl`

`STATUS.md` 只是快照；任何结论都能从上述文件重新算出。

## 项目总览 `PROJECT.md`

`STATUS.md` 面向“逐集/逐项查账”，`PROJECT.md` 面向“不开 agent 也能快速看懂项目”。它由单独脚本生成：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/overview.py <slug> --write
```

`status.py --write` 会同步刷新 `PROJECT.md`。内容包含：项目目标、五乐章计划、接下来 3 集、当前进度、最近完成、故事现在到哪、质量风险、文件导航、最近决策。

## 输出怎么读

| 区块 | 含义 |
|------|------|
| 总览 | 剧名、规模、已通过集数、当前集、下一步、决策条数 |
| 故事进行到哪 | 上一集末价值、留下的问题、主角已知/判断/起疑、下一集钩子 |
| 五乐章进度 | 每乐章已通过集数与进度条 |
| 逐集进度 | `✔` 已通过、`◐` 制作中、`✖` 待修复、`·` 未开始、`!` 异常 |
| 伏笔账本 | 按 `planted_at` / `planned_payoff` 与已写剧本集数推算状态 |
| 人物状态 | 最新集末 `state.yaml` 的地点、已知条数、关系变化、在场状态 |
| 质量与评审 | 每集剧本时长、评审分、轮次、自评/独立、未解决 warning 数 |
| 数据健康 | 标题待定、伏笔状态字段失真、总分不一致、时长超标、自评等 |
| 下一步 | 当前集应进入的 S5/S6/S7 动作，以及可打磨项 |

## 判定规则

**逐集状态**（按文件存在性）：

| 条件 | 状态 |
|------|------|
| 无 `cards.yaml` | 未开始 |
| 有 `cards.yaml`，无 `script.md` | 场景卡完成 |
| 有 `script.md`，无 `review.yaml` | 待评审 |
| `review.verdict=needs_revision` | 待修复 |
| `review.verdict=approved` | 已通过 |
| 已通过但缺 `state.yaml` 等 | 产物异常 |

**伏笔状态**：

1. 账本显式标 `paid` / `dropped` → 直接采用
2. `planted_at` 在已写剧本集数内 → 已埋设；`planned_payoff` 也在已写集数内 → 已回收
3. `planted_at` 晚于最新已写集 → 待埋设
4. 已过 `planned_payoff` 仍未回收 → 逾期未收

注意：`threads.yaml` 里的 `status: planted` 可能只是建账时的默认值，**不能直接相信**；看板会按集数重算，并在“数据健康”里提示。

## 数据健康检查

脚本会主动列出：

- `project.yaml` 标题为空或“待定”
- 伏笔 `status=planted` 但 `planted_at` 晚于最新已写集
- `review.total` 与 8 维合计不一致
- `approved` 但 issues 里仍有 blocker
- 自评评审（reviewer 含 `self`）
- 剧本超过单集时长 +20% 上限
- 卡片预估与成稿时长偏差超过 20%
- 已通过但缺 `state.yaml`
- `hooks.yaml` 条数与项目集数不一致
- `movements.yaml` 未覆盖全部集数
- `decisions.jsonl` 缺失

## 回答用户的方式

1. 先给一句结论：**“目前 X/70 集已通过，当前在 eNN，下一步是……”**
2. 再给 3–6 条关键信息：当前故事价值、下一集钩子、伏笔进度、质量风险
3. 用户要看全表时，再贴 `--full` 输出或指向 `STATUS.md`
4. 不把整份看板原样粘进对话，除非用户明确要“完整看板”

## 与 validate.py 的分工

| 工具 | 职责 |
|------|------|
| `validate.py` | 硬闸门：产物是否合规，能否推进 |
| `status.py` | 只读汇总：现在到哪了、还差什么、风险在哪 |

状态看板不替代校验；看板显示“已通过”不等于重新跑过校验。推进前仍按 SKILL.md 的铁律跑 `validate.py`。
