# W5.2 场景视觉层 · 分镜 · 导出 · 可写操作（设计）

> 立项：2026-11-11 ｜ 状态：设计完成，待实施 ｜ 进度权威：`PLAN.md`
> 相关：`PLAN.md` 第 7 节、`references/data-model.md`、`references/stage-card.md`、
> `references/stage-script.md`、`docs/deliverables.md`

## 1. 为什么要做

当前剧本是**对白演出稿**：`script.md` 只有场景标题、在场人物、节拍、动作和台词。
这是刻意设计（`stage-script.md` 禁止心理活动和旁白），对 90 秒竖屏短剧本身没错，
但带来三个缺口：

1. **场景细节无处承载**：`cards.yaml` 的 `location` 只是一个地名标签，没有环境、陈设、
   光线、声音、道具、服装、走位。
2. **世界设定没进上下文**：`stage-script.md` 的输入清单没有 `bible/world.md`，
   世界规则里的空间、日常质感、代价限制从未喂给写剧本的模型。
3. **没有拍摄层**：没有分镜、景别、机位、镜头时长，导演/摄影/美术拿到剧本无法直接开工；
   `exports/` 也仍是空目录，没有固定导出格式。

评审的 8 维 rubric 同样不考核画面，所以“整集都是某某说”也能拿满分。

## 2. 范围与非目标

### 范围

- 给场景卡补**视觉字段**，让“这场戏长什么样”成为可校验的合同。
- 新增**分镜表** `shots.yaml`，把剧本翻译成可拍的镜头序列。
- 新增**导出器**，产出拍摄稿、分镜表、道具/美术清单。
- 最后再开放**受限可写操作**（批注、卡片字段），且必须留痕、可回滚。

### 非目标

- 不做成片、不做 AI 生图/生视频、不做发布对接。
- 不把 `script.md` 改写成小说：心理活动、文学化比喻仍然禁止。
- 不让 Web 端自由编辑剧本正文，避免绕过 S6/S7 闸门。

## 3. 数据流

```
world.md / voice.md ─┐
cards.yaml（+视觉字段）├─→ S6 剧本 script.md（每场含【场景】描述）
state.yaml ──────────┘        │
                              ├─→ S6.5 分镜 shots.yaml
                              │        │
                              │        ├─→ exports/eNN-shooting.md
                              │        ├─→ exports/eNN-storyboard.csv
                              │        └─→ exports/eNN-props.md
                              └─→ S7 评审（8 维不变 + 视觉自检 warning）
```

## 4. W5.2a 场景视觉层

### 4.1 `cards.yaml` 新增字段（全部可选，缺失只告警）

```yaml
- scene_id: e01-sc01
  location: 幸福里菜市场大门口
  time: 清晨

  # 新增：3–5 句可拍的环境描述。写空间、陈设、光线、声音、气味、人流；
  # 不写心理活动，不写“仿佛/宛如”式比喻。
  scene_description: |
    凌晨五点半，市场刚亮灯。水泥地上是隔夜的鱼鳞和鞭炮红纸屑，
    水氧机在脚边嗡嗡响，白炽灯管有一根在闪。
    对面超市的充气拱门把晨光染成一片塑料红，喇叭循环播放开业促销。

  # 新增：本场关键道具。id 必须与 state.yaml 的 props 键一致。
  props:
    - id: fish-tank
      name: 鱼摊水箱
      state: 水面漂着鞭炮纸屑
      holder: zhou-liping
    - id: scale
      name: 电子秤
      state: 秤盘空着，红字 0.00
      holder: zhou-liping

  # 新增：必须被镜头看到的 2–3 个视觉细节（后续由 shots.yaml 逐条覆盖）。
  visual_beats:
    - 鞭炮纸屑飘进水箱，水面荡开一圈红
    - 老周捞纸屑的手停半秒，水珠从指缝滴回水箱
```

### 4.2 生成规则（S5）

1. 先读 `bible/world.md` 的“空间 / 日常质感”，再写 `scene_description`。
2. `scene_description` 只写**摄影机拍得到**的东西；禁止“他心里一沉”这类心理描写。
3. 每场至少 1 个 `props`、2 个 `visual_beats`；道具 id 与 `state.yaml` 对齐。
4. `visual_beats` 必须服务本场的 `turn`，不能是纯装饰。

### 4.3 生成规则（S6）

1. 输入清单增加 `bible/world.md`。
2. 每场标题和人物行之后，先写一行 `【场景】…`，内容来自 `scene_description`，
   可压缩到 1–3 句，但不得新增未在卡片中出现的关键设定。
3. `visual_beats` 必须在正文中至少各出现一次（动作或特写提示）。
4. 仍然禁止心理活动、解释潜台词、旁白式说明。

示例：

```markdown
## 场景 1：幸福里菜市场大门口 · 清晨
（老周、黄会长）
【场景】凌晨五点半，市场刚亮灯。地上是隔夜鱼鳞和鞭炮红纸屑，水氧机嗡嗡响；对面超市的充气拱门把晨光染成塑料红。

【节拍 1 · 打破平衡】
鞭炮纸屑飘进鱼摊水箱，水面荡开一圈红。老周刀一捞——手停了半秒。
```

### 4.4 校验规则（validate.py）

| 规则 | 级别 | 条件 |
|---|---|---|
| C9-scene-description | WARN | `scene_description` 缺失或少于 20 个汉字（旧集不阻断） |
| C9-visual-beats | WARN | `visual_beats` 少于 2 条 |
| C9-props | BLOCKER | `props` 不是数组，或元素缺 `id`/`name` |
| C9-props-unknown | WARN | `props[].id` 不在 `state.yaml` 的 `props` 键中 |
| C9-script-scene | WARN | 剧本某场缺少 `【场景】` 行（旧集不阻断） |
| W8-visual-beat-miss | WARN | `visual_beats` 中的关键词在剧本正文中完全找不到 |

> 原则：新字段先以 WARN 引入，回填完成后在下一个大版本升为 BLOCKER。

## 5. W5.2b 分镜表（S6.5）

### 5.1 产物：`episodes/eNN/shots.yaml`

```yaml
- shot_id: e01-s01-k01
  scene_id: e01-sc01          # 必须存在于 cards.yaml
  shot_no: 1                  # 集内连续，从 1 开始
  shot_size: 特写             # 大远景/远景/全景/中景/近景/特写/大特写
  camera: 固定                # 固定/手持/推/拉/摇/移/跟
  angle: 平视                 # 平视/俯拍/仰拍/过肩/主观
  duration: 3                 # 秒，整数
  picture: 鞭炮纸屑落进鱼摊水箱，水面荡开一圈红
  dialogue: ""                # 台词原文或摘要；无台词留空
  sound: 画外锣鼓、宣传车喇叭
  props: [fish-tank]          # 引用 cards.yaml 的 props id
  visual_beat: 鞭炮纸屑飘进水箱，水面荡开一圈红
  transition: 硬切             # 硬切/叠化/黑场/划像
```

### 5.2 生成规则

1. 输入：`script.md` + `cards.yaml` + `world.md` + `voice.md`。
2. 一场至少 3 个镜头；集内镜头总时长落在 72–108 秒（`seconds_per_episode` ±20%）。
3. 每个 `visual_beats` 至少被一个镜头覆盖；每个 `must_happen` 至少被一个镜头覆盖。
4. 竖屏构图优先：近景/特写为主，全景只用于交代空间。
5. 台词可拆分到多个镜头，但不得改写台词内容。

### 5.3 校验规则（新增 `--stage shots`）

| 规则 | 级别 | 条件 |
|---|---|---|
| S1-shot-no | BLOCKER | `shot_no` 不连续或重复 |
| S2-scene-ref | BLOCKER | `scene_id` 不在本集 cards.yaml |
| S3-duration | BLOCKER | 单镜 ≤0 秒，或全集合计不在 ±20% 区间 |
| S4-picture | BLOCKER | `picture` 为空 |
| S5-prop-ref | WARN | `props` 引用了 cards/state 中不存在的 id |
| S6-beat-cover | WARN | 某个 `visual_beats` 没有对应镜头 |
| S7-scene-cover | BLOCKER | 某张场景卡没有任何镜头 |

## 6. W5.2c 导出器

### 6.1 命令

```bash
python scripts/export.py <slug> [--episode N] --kind shooting|storyboard|props --format md|csv|json
```

- 不带 `--episode` 时导出全季（仅 `storyboard` / `props`）。
- 默认输出到 `projects/<slug>/exports/`，可用 `--out` 覆盖。
- 只读事实源，不写回 `episodes/`。

### 6.2 产物与文件名

| kind | format | 文件名 | 内容 |
|---|---|---|---|
| shooting | md | `eNN-shooting.md` | 拍摄稿：场景描述 + 分镜表 + 台词 + 道具 |
| storyboard | csv | `eNN-storyboard.csv` / `season-storyboard.csv` | 镜号、场景、景别、机位、时长、画面、台词、音效、道具 |
| storyboard | json | `eNN-storyboard.json` | 同上，结构化数组 |
| props | md | `eNN-props.md` / `season-props.md` | 按场景汇总道具、状态、持有人、跨集变化 |

### 6.3 CSV 契约

- UTF-8 with BOM（Excel 直接打开不乱码）。
- 首行表头固定：`shot_id,scene_id,shot_no,shot_size,camera,angle,duration,picture,dialogue,sound,props,visual_beat,transition`。
- `props` 多值用 `|` 分隔。
- 字段内换行替换为空格，逗号按 CSV 规则加引号。

### 6.4 外部系统契约

- 字段只增不改；未知字段忽略。
- 导出件不是事实源，可随时重新生成；不要回写。
- 契约细节在实施 W5.2c 时补入 `docs/deliverables.md`。

## 7. W5.2d 可写操作（最后做）

### 7.1 允许写

- 评审批注（`review.yaml` 的 `issues` 追加）。
- 场景卡字段编辑（`cards.yaml` 的文本字段）。
- 决策日志追加（`decisions.jsonl`）。

### 7.2 禁止写

- `script.md` 正文自由编辑（必须走 S6 重新生成）。
- `state.yaml` / `structure/` / `bible/`（必须走对应阶段）。
- 删除集目录、改写历史决策。

### 7.3 安全要求

1. 默认只监听 `127.0.0.1`；对外必须加 token。
2. 写前生成 `.bak`，写后自动跑 `validate.py --stage cards|review --episode N`。
3. 校验失败自动回滚并返回错误。
4. 每次写入追加 `decisions.jsonl`，记录操作者、时间、字段、旧值、新值。
5. 文件锁 + 版本号，防止并发覆盖。

## 8. 向后兼容与回填

- 新字段全部**可选**，旧集不阻断；先用 WARN 暴露缺口。
- 回填顺序：e01 示范 → 用户确认风格 → e02–e10 批量 → 新集默认必填。
- 回填只补视觉字段和 `【场景】` 行，不改台词、不改价值翻转、不改钩子。
- 回填后重跑 `validate.py`、`continuity.py`、`evals/run_evals.py`。

## 9. 验收标准

| 子阶段 | 验收 |
|---|---|
| W5.2a | e01 回填后 `validate --stage cards --episode 1` 与 `--stage script --episode 1` 均 0 blocker；新增 evals 全绿；剧本每场有可拍的 `【场景】` 描述 |
| W5.2b | e01 `shots.yaml` 通过 `--stage shots` 校验；镜头总时长 72–108 秒；每个 `visual_beat` 有镜头覆盖 |
| W5.2c | 三种格式导出成功；CSV 可被表格软件打开；字段与契约一致 |
| W5.2d | 写操作有备份/校验/回滚；越权写被拒绝；Web 默认仍只读 |

## 10. 实施顺序与风险

1. **W5.2a**（先解决“剧本没场景”的痛点，改动最小）
2. **W5.2b**（分镜表，依赖 a 的视觉字段）
3. **W5.2c**（导出，依赖 b 的 shots.yaml）
4. **W5.2d**（可写，风险最高，最后做）

| 风险 | 对策 |
|---|---|
| 新字段让旧集校验变红 | 一律先 WARN，回填后再升 BLOCKER |
| 场景描述写成小说 | 校验长度上限 + 评审加“可拍性”自检 |
| 分镜表与剧本脱节 | `shot_id` 绑定 `scene_id`，台词必须能在剧本中找到 |
| 导出格式频繁变 | 字段只增不改，CSV 表头固定 |
| 可写操作破坏事实源 | 白名单字段 + 备份 + 校验 + 回滚 + 决策日志 |
