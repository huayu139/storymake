# 连续性巡检与集末状态账本（W4）

## 何时使用

- 每写完一集、每完成一个批次（建议每 5 集）后跑一次。
- 用户问“有没有前后矛盾 / 人物怎么跑这儿来了 / 道具去哪了 / 伏笔挂没挂上”时先跑。
- 10 集试播收尾、进入下一乐章前必须跑，作为 W4 的硬验收。

## 命令

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/continuity.py <slug>

# 生成/刷新 projects/<slug>/CONTINUITY.md
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/continuity.py <slug> --write
```

脚本只读 `structure/` 与 `episodes/*/{cards,script,state,review}`，不改事实源；`CONTINUITY.md` 只是快照。

## 输出

| 区块 | 内容 |
|------|------|
| 总览 | 已进入制作集数、BLOCKER / WARN 数、是否通过 |
| 集末状态账本 | 每集剧本秒数、评审、人物位置、道具数、open_threads |
| 人物位置轨迹 | 一个角色逐集的位置变化，一眼看跳变 |
| 道具账本 | 每个道具首次/最近出现、当前状态、持有者 |
| 伏笔挂账 | 埋设/回收集、实际挂账集、账本状态 |
| 问题清单 | K1–K8 逐条列出，带文件定位 |
| 口径说明 | 判定口径，避免“看起来像矛盾”的误报 |

## 规则

### 阻断级（BLOCKER）

| 规则 | 判据 |
|------|------|
| K1 | 有 `script.md` 但缺 `state.yaml` |
| K2 | `dead` / `written_out` 的人物在后续集 `cards.yaml` 的 cast 中复出 |
| K3 | 相邻集价值断链：上集 `value_after` ≠ 下集 `value_before` |
| K4 | `open_threads` 含未登记伏笔，或在该伏笔 `planted_at` 之前提前挂账 |

### 警告级（WARN）

| 规则 | 判据 |
|------|------|
| K4 | 伏笔已过 `planned_payoff` 仍挂账；埋设集未挂账 |
| K5 | 人物集间位置变化，但新旧位置任一片段都没在剧本中出现 |
| K6 | 上集账本有、本集无处置地消失（状态未写消耗/归还/交出/回收/清零） |
| K7 | 剧本按 4.5 字/秒估算，超出目标 ±20% |
| K8 | 有剧本缺评审；`total` 与 8 维合计不一致；`approved` 但仍有 blocker |

## 集末状态账本的写法

- **位置**：写本集最后一个可拍落点，不要写“某地→某地（离开）”这种过程值；剧本里要能找到对应片段。
- **持有物**：只写本集实际带在身上/手边的关键道具；留在原地的道具写进 `props` 的 `holder`，不要从账本消失。
- **knows / believes / suspects**：只记本集剧本实际透露的内容，不写导演层推断。
- **props**：每集延续上一集未回收的道具；状态变化写清楚（如“压在秤盘下”“被段志远持有”）。
- **open_threads**：只挂 `structure/threads.yaml` 里已登记、且 `planted_at <= 当前集` 的伏笔；回收后移除。

## W4 十集试播的收尾标准

1. e01–e10 都有 `cards.yaml / script.md / state.yaml / review.yaml`。
2. `continuity.py` 0 BLOCKER；WARN 逐条人工确认并在 `decisions.jsonl` 留痕。
3. `validate.py --stage all` 0 BLOCKER（含结构、人物、关系）。
4. `evals/run_evals.py` 全绿。
5. 通读 e01–e10，确认价值线、人物知识、道具、伏笔四本账一致。

## 与其它脚本的分工

| 脚本 | 职责 |
|------|------|
| `validate.py` | 单阶段/单集硬闸门：产物是否合规，能否推进 |
| `continuity.py` | 跨集巡检：价值线、位置、道具、伏笔、评审是否接得上 |
| `status.py` | 只读进度看板：做到哪了、还差什么 |

三个脚本都只读事实源；推进前仍以 `validate.py` 的 BLOCKER 清零为准。
