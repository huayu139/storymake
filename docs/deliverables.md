# Story Lab 交付件与集成说明

> 面向：需要使用本工作台产物的外部系统（导出器、发布系统、审核后台、可视化面板等）。
> 定位：一份说清“有哪些文件、每个文件是什么、字段怎么读、如何稳定集成”的交接文档。
> 最后更新：2026-11-10
> 相关文档：`docs/architecture.md`（分层与铁律）、`.opencode/skill/story-workbench/references/data-model.md`（字段样例）、`.opencode/skill/story-workbench/SKILL.md`（创作工作流）。

---

## 0. 先看这五条

1. **事实源只有一个**：`projects/<slug>/` 下的 `project.yaml`、`bible/`、`structure/`、`episodes/`、`decisions.jsonl`。
2. **三份 Markdown 只是快照，不可当事实源**：`PROJECT.md`、`STATUS.md`、`CONTINUITY.md` 由脚本生成，可能过期。
3. **推荐只读消费**：外部系统不要写这些文件；创作与修改由工作台负责。
4. **未知字段请忽略**：字段只增不改，兼容靠“忽略未知、保留原文”。
5. **两套读取入口**：直接读文件（零耦合），或调用 `status.py` / `webview.py`（已封装汇总）。

---

## 1. 交付件分类

| 类型 | 路径 | 是否事实源 | 生成方式 | 外部系统建议 |
|---|---|---|---|---|
| 项目配置 | `projects/<slug>/project.yaml` | ✅ | 人工/工作台 | 必读 |
| 故事圣经 | `projects/<slug>/bible/` | ✅ | S1–S3 | 必读 |
| 结构 | `projects/<slug>/structure/` | ✅ | S4 | 必读 |
| 分集产物 | `projects/<slug>/episodes/eNN/` | ✅ | S5–S7 | 必读 |
| 决策日志 | `projects/<slug>/decisions.jsonl` | ✅ | 追加式 | 建议读 |
| 快照 | `PROJECT.md` / `STATUS.md` / `CONTINUITY.md` | ❌ | 脚本生成 | 可选，勿当事实源 |
| 校验工具 | `scripts/validate.py` | — | 只读 | 可选，消费前自检 |
| 汇总工具 | `scripts/status.py` | — | 只读 | 推荐复用 |
| 对账工具 | `scripts/continuity.py` | — | 只读 | 跨集场景推荐 |
| 提示词导出 | `scripts/prompt.py` | — | 只读 | 生图/生视频提示词拼装（锚点+卡片+人物四件套） |
| Web API | `scripts/webview.py` | — | 只读 | 适合前端/远程消费 |
| 回归测试 | `evals/run_evals.py` | — | 只读 | 开发期使用 |

---

## 2. 目录清单

```text
projects/<slug>/
├── project.yaml                  # 项目元信息（必读）
├── decisions.jsonl               # 决策日志，每行一个 JSON
├── bible/
│   ├── premise.md                # 立意：logline、引擎、选择理由
│   ├── characters/<id>.yaml      # 人物卡，一人一文件
│   ├── relations.yaml            # 关系边数组
│   ├── world.md                  # 世界规则
│   └── voice.md                  # 文风、禁用词
├── structure/
│   ├── movements.yaml            # 五乐章 + 钉死集
│   ├── hooks.yaml                # 70 集钩子表
│   └── threads.yaml              # 伏笔账本
├── episodes/eNN/                 # e01、e02……零填充两位
│   ├── cards.yaml                # 场景卡数组
│   ├── script.md                 # 剧本正文
│   ├── state.yaml                # 集末状态与角色知识
│   └── review.yaml               # 评审
├── STATUS.md                     # 快照（非事实源）
├── PROJECT.md                    # 快照（非事实源）
├── CONTINUITY.md                 # 快照（非事实源）
└── exports/                      # 预留导出目录（当前可为空）
```

### 文件必读性

| 文件 | 何时存在 | 缺失时含义 |
|---|---|---|
| `project.yaml` | 项目创建即有 | 不是有效项目，跳过 |
| `bible/premise.md` | S1 完成后 | 还没立意 |
| `bible/characters/*.yaml` | S2 完成后 | 还没人物 |
| `bible/relations.yaml` | S3 完成后 | 还没关系网 |
| `structure/hooks.yaml` | S4 完成后 | 还没结构 |
| `episodes/eNN/cards.yaml` | 该集 S5 完成 | 该集未开始 |
| `episodes/eNN/script.md` | 该集 S6 完成 | 该集没剧本 |
| `episodes/eNN/state.yaml` | 该集 S6 完成 | 账本缺失，属异常 |
| `episodes/eNN/review.yaml` | 该集 S7 完成 | 该集未评审 |

---

## 3. 核心数据契约

> 完整样例见 `.opencode/skill/story-workbench/references/data-model.md`。下面只列外部系统必须知道的字段与不变量。

### 3.1 `project.yaml`

| 字段 | 类型 | 说明 |
|---|---|---|
| `slug` | string | 项目唯一 ID，与目录名一致 |
| `title` | string | 剧名 |
| `genre` | string | 题材，如“都市逆袭” |
| `platform` | string | 平台，如“竖屏短剧” |
| `episodes` | int | 总集数 |
| `seconds_per_episode` | int | 单集目标秒数（当前 90） |
| `audience` | string | 受众描述 |
| `taboos` | string[] | 禁忌清单 |
| `persona` | string | 创作人格（工作台内部用） |
| `created` | date | 创建日期（YAML date，JSON 化后为 `YYYY-MM-DD`） |

### 3.2 人物卡 `bible/characters/<id>.yaml`

必读字段：`id`、`name`、`role`、`want`、`fear`、`secret`、`lie`、`wound`、`arc`、`voice_samples`、`progressions`、`visible_from`。

- `role` 取值：`protagonist` / `antagonist` / `supporting`。
- `progressions` 是数组，元素为 `{at: eNN, state: "..."}`，表示该人物在该集的状态节点。
- `visible_from` 表示该人物卡从第几集起才允许进入生成上下文，外部系统可据此做剧透控制。
- `id` 是稳定主键，关系网与 state 都引用它。

### 3.3 关系 `bible/relations.yaml`

数组元素字段：`from`、`to`、`type`、`power_diff`、`dependency`、`unsaid`、`tension`、`flip_episode`。

- `from` / `to` 均为人物 `id`。
- `flip_episode` 为预计翻转集；0 或缺失表示未定。

### 3.4 结构 `structure/movements.yaml`

```yaml
movements:
  - {id: 1, name: "铺垫与第一战", episodes: [1, 14], goal: "..."}
pinned_episodes:
  - {episode: 10, kind: 付费卡点, note: "..."}
```

- `episodes` 是闭区间 `[起始集, 结束集]`。
- `pinned_episodes` 的 `kind` 当前有：`付费卡点`、`中点`、`一无所有`、`大结局`。

### 3.5 钩子表 `structure/hooks.yaml`

数组元素：`episode`、`movement`、`question_raised`、`question_left_open`、`cliffhanger_type`、`value_before`、`value_after`、`pinned`。

- `question_left_open` 是该集结尾必须留给观众的问题，外部系统做预告/标题时优先用它。
- `cliffhanger_type` 四选一：`揭露` / `反转` / `倒计时` / `闯入`。
- 相邻集不得同类型；`value_after` 必须等于下一集 `value_before`。

### 3.6 伏笔账本 `structure/threads.yaml`

数组元素：`id`、`type`、`planted_at`、`planned_payoff`、`status`、`description`，可选 `note`。

- `status`：`planted` / `building` / `paid` / `dropped`。
- `planned_payoff` 必须大于 `planted_at`。
- 已知账本问题：部分 `status=planted` 的 `planted_at` 晚于最新已写集，消费时建议以“已写集范围 + planted_at/planned_payoff”重新推算，不要只信 `status`。

### 3.7 场景卡 `episodes/eNN/cards.yaml`

数组，每个元素是一场戏：

| 字段 | 类型 | 说明 |
|---|---|---|
| `scene_id` | string | 如 `e10-sc01` |
| `pov` | string | 视角人物 id |
| `location` | string | 地点 |
| `time` | string | 时间 |
| `cast` | string[] | 出场人物 id |
| `objective` | string | 本场目标 |
| `obstacle` | string | 本场阻碍 |
| `value_before` / `value_after` | string | 价值翻转，必须不同 |
| `must_happen` | string[] | 必须发生 |
| `must_not_happen` | string[] | 禁止发生 |
| `information_delta` | object | 人物 id / `audience` / `hidden` → 信息变化 |
| `turn` | string | 本场转折 |
| `cliffhanger_type` | string | 仅该集最后一场必填 |
| `estimated_seconds` | int | 预估秒数 |

### 3.8 剧本 `episodes/eNN/script.md`

- 纯 Markdown，UTF-8。
- 结构：一级标题（集名）→ `## 场景 N：地点 · 时间` → `【节拍 …】` → 台词/动作。
- 台词格式为 `角色名：台词`；动作用全角括号或普通段落。
- **时长口径**：`cjk_len / 4.5`，其中 `cjk_len = 汉字数 + 英文单词数`。
- 验收区间：`target × 0.8 ≤ 时长 ≤ target × 1.2`；当前 target=90，即 **72–108 秒**。

### 3.9 集末状态 `episodes/eNN/state.yaml`

```yaml
characters:
  <character-id>:
    location: string
    injured: bool
    holds: string[]              # 道具 key
    relationship_changes: string[]
    dead: bool
    written_out: bool
    knows: string[]              # 本集后确知
    believes: string[]           # 本集后判断
    suspects: string[]           # 本集后起疑
    must_not_know: string[]      # 硬约束
props:
  <prop-key>: {status: string, holder: string}
open_threads: [t-01, t-02]
```

- `knows` / `believes` / `suspects` 是自然语言数组，不保证枚举化；外部系统应视为展示文本。
- `props.holder` 是人物 id；空字符串表示无持有者/公共位置。
- `open_threads` 是该集结束时仍未回收的伏笔 id。

### 3.10 评审 `episodes/eNN/review.yaml`

核心字段：`round`、`episode`、`reviewer`、`summary`、`scores`、`total`、`threshold`、`verdict`、`issues`。

- `scores` 固定 8 维：`hook`、`causality`、`character_consistency`、`voice_distinctness`、`value_shift`、`information_management`、`emotional_payoff`、`originality`。
- 每维 `{score: 1-5, evidence: "引用原文的证据"}`。
- `threshold` 当前为 32（8 维 × 4 分）。
- `verdict`：`approved` / `needs_revision`。
- `issues` 数组元素：`code`、`severity`（`blocker` / `warning`）、`evidence`、`location`。
- 可能出现扩展审计字段：`round1_total`、`round1_verdict`、`blocker_count`、`final_fix_audit`、`contract_check`、`state_check`、`thread_check`、`duration_check`、`paid_pin_check` 等；外部系统可忽略未知字段。
- 通过判定建议：`verdict == approved` 且 `total >= threshold` 且无未解决 blocker。`force_pass` 也是 approved，但理由在 `decisions.jsonl`。

### 3.11 决策日志 `decisions.jsonl`

每行一个 JSON，追加式，不要重排：

```json
{"ts":"2026-11-05T09:05:00Z","stage":"review","episode":10,"action":"approve","chosen":"e10/review.yaml round3 32/32 approved","alternatives":["..."],"reason":"...","persona":"爽感派","model":"agent"}
```

- `action`：`select` / `revise` / `regenerate` / `reject` / `approve` / `force_pass` / `sync` / `complete` / `add`。
- 外部系统读取时按行解析，允许空行；解析失败不要中断整批，记录原始行即可。

### 3.12 快照文件

| 文件 | 生成命令 | 用途 |
|---|---|---|
| `PROJECT.md` | `overview.py <slug> --write` | 项目总览（目标/乐章/当前进度） |
| `STATUS.md` | `status.py <slug> --write` | 全季状态看板 |
| `CONTINUITY.md` | `continuity.py <slug> --write` | 跨集巡检账本 |

> 这三份文件带生成时间戳，可能落后于事实源。**外部系统应重新计算，或至少比对 mtime 后再用。**

---

## 4. 如何判断项目与单集状态

| 判据 | 所处阶段 |
|---|---|
| 无 `bible/premise.md` | S1 立意 |
| `premise.md` 有，人物卡不足 3 份 | S2 人物 |
| 人物齐，无 `relations.yaml` | S3 关系 |
| 关系有，无 `structure/hooks.yaml` | S4 结构 |
| 结构有，无 `episodes/e01/cards.yaml` | S5 场景卡 |
| `cards.yaml` 有，无 `script.md` | S6 剧本 |
| `script.md` 有，无 `review.yaml` | S7 评审 |
| `review.verdict == approved` | 该集通过，进入下一集 |
| 全部集通过 | 全季完成 |

单集状态建议按以下顺序判定：

```text
无 cards.yaml           -> 未开始
无 script.md            -> 场景卡完成
无 review.yaml          -> 待评审
review.verdict != approved -> 待修复
review.verdict == approved -> 已通过
```

---

## 5. 三种集成方式

### 方式 A：直接读文件（推荐，零耦合）

适合导出器、发布系统、审核后台。

```python
from pathlib import Path
import yaml

def load_episode(proj: Path, ep: int) -> dict:
    d = proj / f"episodes/e{ep:02d}"
    read = lambda name: (d / name).read_text(encoding="utf-8") if (d / name).exists() else ""
    yaml_or_none = lambda name: yaml.safe_load(read(name)) if (d / name).exists() else None
    return {
        "ep": ep,
        "cards": yaml_or_none("cards.yaml"),
        "script": read("script.md"),
        "state": yaml_or_none("state.yaml"),
        "review": yaml_or_none("review.yaml"),
    }
```

约定：
- 用 `safe_load`，不要 `load`。
- 所有文件按 UTF-8 读取。
- 集目录名固定 `eNN`，两位数零填充。
- 缺失文件用 `None`/空列表表示，不要当解析失败。

### 方式 B：复用 Python 汇总函数

适合需要“已经算好的进度/伏笔/质量”的系统。

```python
import sys
from pathlib import Path

sys.path.insert(0, ".opencode/skill/story-workbench/scripts")
import status as st

proj = Path("projects/urban-counterattack")
data = st.build_dataset(proj)

print(data["n_eps"])                 # 总集数
print(data["episodes"][9]["status"]) # e10 状态
print(st.thread_rows(data))          # 伏笔推算
print(st.health_checks(data))        # 数据健康
```

- `build_dataset()` 返回的 `data["proj"]` 是 `Path`，序列化前要转字符串。
- `episode_info()` 里的 `script` 是布尔值，不是正文；要正文请直接读 `script.md`。
- 该函数只读，不修改文件。

### 方式 C：HTTP API（适合前端或跨进程/跨主机）

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/webview.py --host 0.0.0.0 --port 8765
```

| 方法 | 路径 | 返回 |
|---|---|---|
| GET | `/api/health` | `{ok, root, projects, time}` |
| GET | `/api/projects` | `{projects: [{slug, title, genre, episodes, seconds_per_episode, errors}]}` |
| GET | `/api/project/<slug>/overview` | 总览：`project`、`logline`、`progress`、`movements`、`pinned`、`next`、`story`、`recent`、`quality`、`threads`、`generated` |
| GET | `/api/project/<slug>/episodes` | `{project, episodes: [单集摘要]}` |
| GET | `/api/project/<slug>/episode/<n>` | `{project, summary, hook, cards, script, state, review, character_names}` |
| GET | `/api/project/<slug>/bible` | `{project, premise, world, voice, characters, relations}` |
| GET | `/api/project/<slug>/structure` | `{project, movements, pinned, hooks, threads}` |
| GET | `/api/project/<slug>/continuity` | `{project, latest, blockers, warnings, issues, episodes}` |
| GET | `/api/project/<slug>/decisions` | `{total, decisions: [...]}` |

单集摘要字段：

```json
{
  "ep": 10, "status": "已通过", "raw_status": "通过",
  "scenes": 2, "script_seconds": 107.6,
  "review_total": 32, "review_threshold": 32,
  "review_verdict": "approved", "warnings": 3, "blockers": 0,
  "hook": "代签的笔迹，竟和老周一模一样？",
  "cliffhanger": "反转",
  "value_before": "团结", "value_after": "背叛感",
  "pinned": true
}
```

- 服务只读，不提供写接口。
- 数据每次请求实时读盘，没有缓存；响应带 `Cache-Control: no-store`。
- 路径参数 `slug` 只允许 `[A-Za-z0-9_-]`。

---

## 6. 字段稳定性与兼容约定

1. **只增不改**：新增字段不破坏旧消费方；消费方必须忽略未知字段。
2. **枚举兜底**：未知 `status` / `verdict` / `cliffhanger_type` 不要崩溃，按“未知”展示。
3. **主键稳定**：`slug`、人物 `id`、伏笔 `id`、`scene_id`、集号 `ep` 是稳定标识。
4. **集号格式**：路径用 `eNN`，数值字段用 int。
5. **YAML 日期**：`created` 可能被解析为 `date`；JSON 化时转 ISO 字符串。
6. **快照不参与判定**：进度、通过与否一律从事实源重算。
7. **追加日志不重排**：`decisions.jsonl` 保持追加顺序；外部系统若要合并，按 `ts` 排序但保留原始行。
8. **版本字段**：人物卡有 `version`；产物修改应递增并在决策日志留理由。

---

## 7. 外部系统推荐流程

```text
启动
  → 扫描 projects/*/project.yaml
  → 读取 project.yaml + structure/hooks.yaml
  → 逐集检查 cards/script/state/review 是否存在
  → 计算单集状态与全季进度
  → 需要展示时读取 cards/script/state/review 正文
  → 需要跨集一致性时调用 continuity 逻辑或读 CONTINUITY.md
  → 需要“当前故事到哪”时读最后一集 state + hooks
```

刷新策略：
- 文件监听（mtime）或每次打开详情时重读，避免长缓存。
- 不要缓存 `PROJECT.md` / `STATUS.md` 的结论而不校验时间戳。
- 写操作不要在外部系统做；如需验收/修改，回到工作台写文件并追加 `decisions.jsonl`。

---

## 8. 消费前最小自检

| 检查 | 期望 |
|---|---|
| `project.yaml` 可解析 | `slug`、`episodes`、`seconds_per_episode` 存在 |
| 集目录命名 | `e01`…`e70`，两位数 |
| `cards.yaml` | 数组；每场 `value_before != value_after` |
| `script.md` | 存在时有 `角色名：台词` 结构 |
| 时长 | `cjk_len / 4.5` 落在 72–108 秒 |
| `state.yaml` | `characters`、`props`、`open_threads` 存在 |
| `review.yaml` | 8 维 `scores` 齐全；`total` 与分数和一致 |
| 通过判定 | `verdict == approved` 且 `total >= threshold` |
| 决策日志 | 每行可独立解析为 JSON |

如需强校验，直接运行：

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/validate.py urban-counterattack

/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/continuity.py urban-counterattack
```

---

## 9. 已知限制

- `PROJECT.md` / `STATUS.md` / `CONTINUITY.md` 是快照，时间戳可能落后。
- 部分伏笔的 `status=planted` 与 `planted_at` 不一致；以集号推算为准。
- 评审文件存在扩展审计字段，不同集字段不完全一致；只依赖核心字段。
- `knows` / `believes` / `suspects` 是自然语言，不能当结构化事实库。
- `exports/` 目前是预留目录，尚无固定导出格式。
- Web 查看器是只读 MVP，没有鉴权；对外暴露时请放在内网或反向代理后。
- 当前没有独立 JSON Schema 文件；本文件 + `data-model.md` 即契约。

---

## 10. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-10 | 初版：交付件分类、文件清单、核心 schema、三种集成方式、API 契约、兼容约定与自检清单 |
