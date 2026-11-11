# 数据模型与文件约定

> 给外部系统消费时，先看 `docs/deliverables.md`（交付件分类、集成方式、API 契约、兼容约定）。

## 1. 项目目录

```
projects/<slug>/
├── project.yaml          # 项目配置（init 时创建）
├── decisions.jsonl       # 决策日志，追加式，每行一个 JSON
├── bible/
│   ├── premise.md        # S1 产物：logline + 引擎 + 选择理由
│   ├── characters/*.yaml # S2 产物：一人一卡
│   ├── relations.yaml    # S3 产物：关系边数组
│   ├── world.md          # 世界规则（S1/S2 间补充）
│   └── voice.md          # 文风与禁用词（S1 时确定）
├── structure/
│   ├── movements.yaml    # S4 产物：五乐章
│   ├── hooks.yaml        # S4 产物：分集钩子表
│   └── threads.yaml      # S4 产物：伏笔账本
├── episodes/eNN/
│   ├── cards.yaml        # S5 产物：场景卡数组
│   ├── script.md         # S6 产物：剧本正文
│   ├── state.yaml        # S6 产物：集末状态 + 知识状态
│   └── review.yaml       # S7 产物：8 维评审
├── STATUS.md             # 状态看板快照（status.py --write 生成，非事实源）
├── PROJECT.md            # 项目总览快照（overview.py --write / status.py --write 生成，非事实源）
├── CONTINUITY.md         # 连续性巡检快照（continuity.py --write 生成，非事实源）
└── exports/
```

## 2. 阶段状态判断（读文件即知进度）

| 判据 | 所处阶段 |
|------|----------|
| 无 bible/premise.md | S1 立意 |
| premise.md 有，characters/ 不足 3 份 | S2 人物 |
| characters 齐，relations.yaml 无 | S3 关系 |
| relations 有，structure/hooks.yaml 无 | S4 结构 |
| hooks 有，episodes/e01/cards.yaml 无 | S5 场景卡（从 e01 开始） |
| cards 有，e01/script.md 无 | S6 剧本 |
| script 有，e01/review.yaml 无 | S7 评审 |
| review verdict=approved | 下一集的 S5，或全季完成 |

> 想一次看全季进度、伏笔、人物与评审状态：运行 `scripts/status.py <slug>`（只读汇总，见 `stage-status.md`）。
> 想看跨集是否接得上：运行 `scripts/continuity.py <slug>`（集末状态账本 + K1–K8 巡检，见 `stage-continuity.md`）。
> 需要文件时加 `--write`，生成 `projects/<slug>/STATUS.md` 或 `CONTINUITY.md`；两者只是快照，事实源仍是上面的 YAML/Markdown。

## 3. 核心 Schema（YAML）

### project.yaml

```yaml
slug: dashang-jie
title: 待定
genre: 都市逆袭
platform: 竖屏短剧
episodes: 10            # 首季集数
seconds_per_episode: 90
audience: 25-35 女性
taboos: [过度血腥, 明星影射]
created: 2026-11-03
```

### character.yaml（bible/characters/<id>.yaml）

```yaml
id: lin-wan
name: 林晚
role: protagonist        # protagonist/antagonist/supporting
want: 找到姐姐车祸的真相        # 外在目标
fear: 发现真相会毁掉唯一还在的人 # 内在恐惧
secret: 她三年前隐瞒了一段通话记录
lie: 我只是想查清楚，不为别的   # 对自己撒的谎
wound: 姐姐车祸当晚她没接电话   # 创伤
arc: 从逃避到直面             # 人物弧线一句话
voice_samples:              # 5 句只有他会说的话
  - 我不要解释，我要证据。
  - 你早就知道了，对吧？
voice_rules: [短句, 不用感叹号, 偶尔自嘲]
never_say: [你听我解释]      # 5 句他绝不会说的话（至少 2 句）
progressions:               # NovelCrafter 式：状态随时间变化
  - { at: e01, state: "对顾彦辰半信半疑" }
  - { at: e06, state: "确认顾彦辰在隐瞒" }
visible_from: 1             # 该卡从第几集起对模型可见（防剧透）
version: 1
```

### relation（bible/relations.yaml 数组元素）

```yaml
from: lin-wan
to: gu-yanchen
type: 前恋人/现任对峙
power_diff: gu-yanchen 占优    # 权力差谁占优
dependency: 林晚需要他的资源    # 依赖关系
unsaid: 他三年前就见过姐姐     # 未说出口的话
tension: 每次对话都在试探
flip_episode: 6                # 预计翻脸/反转集（0=未定）
```

### hook（structure/hooks.yaml 数组元素）

```yaml
episode: 3
movement: 2                     # 所属乐章 1-5
question_raised: 姐姐的通话记录里为什么有顾彦辰？
question_left_open: 谁把存储卡拿走了？   # 必填，结尾必须留问题
cliffhanger_type: 揭露          # 揭露/反转/倒计时/闯入 四选一，相邻集不得重复
value_before: 信任
value_after: 怀疑
pinned: false                   # 是否钉死集（付费卡点/中点/一无所有/大结局）
```

### thread（structure/threads.yaml 数组元素）

```yaml
id: t-01
type: 伏笔/悬念
planted_at: 1                   # 埋设集
planned_payoff: 6               # 计划回收集（必须 > planted_at）
status: planted                 # planted/building/paid/dropped
description: 行车记录仪的存储卡
```

### scene_card（episodes/eNN/cards.yaml 数组元素）

```yaml
scene_id: e01-sc01
pov: lin-wan                    # 视角人物
location: 地下车库
time: 夜
cast: [lin-wan, gu-yanchen]
objective: 林晚要拿到行车记录仪   # 本场目标
obstacle: 顾彦辰先到一步，且知道她在找什么
value_before: 被动/被控制
value_after: 主动/掌握筹码       # 必须 != value_before
must_happen:
  - 林晚发现存储卡已经被拿走
  - 她说出"你早就知道"的试探
must_not_happen:
  - 不能揭露顾彦辰是幕后的人
  - 不能发生肢体冲突
information_delta:              # 信息差：谁知道什么
  lin-wan: 确认顾彦辰在隐瞒
  gu-yanchen: 知道林晚开始怀疑
  audience: 看到顾彦辰口袋里的卡
  hidden: 顾彦辰的真实身份       # 观众和角色都不知道的
turn: 林晚假装放弃，却在车上留下录音笔
cliffhanger_type: 揭露          # 仅该集最后一场必填
```

### state（episodes/eNN/state.yaml）

```yaml
characters:
  lin-wan:
    location: 车内
    injured: false
    holds: [录音笔]
    relationship_changes: ["与顾彦辰信任 → 怀疑"]
    knows:                      # 生成对白时只注入这三项
      - 顾彦辰今晚出现在车库
      - 行车记录仪被人动过
    believes:
      - 顾彦辰在替别人做事
    suspects:
      - 顾彦辰和姐姐的死有关
    must_not_know:              # 硬约束，写进演员提示
      - 顾彦辰的真实身份
      - 存储卡在他口袋里
props:
  dashcam: { status: 被拿走, holder: gu-yanchen }
open_threads: [t-01]            # 本集结束时未回收的伏笔
```

### review（episodes/eNN/review.yaml）

```yaml
round: 1
scores:                          # 每项 1-5，必须附 evidence
  hook: { score: 4, evidence: "开场 3 秒婚礼现场冲突" }
  causality: { score: 5, evidence: "因为存储卡缺失，所以她试探顾彦辰" }
  character_consistency: { score: 4, evidence: "…" }
  voice_distinctness: { score: 4, evidence: "…" }
  value_shift: { score: 5, evidence: "被动 → 掌握筹码" }
  information_management: { score: 3, evidence: "第 3 段台词疑似泄底" }
  emotional_payoff: { score: 4, evidence: "…" }
  originality: { score: 4, evidence: "…" }
issues:
  - code: info-leak
    severity: warning            # blocker/warning
    evidence: "台词直接说出了顾彦辰的身份"
    location: script.md#L42
verdict: needs_revision          # needs_revision/approved
total: 33
```

## 4. 决策日志（decisions.jsonl，每行一个 JSON）

```json
{"ts":"2026-11-03T12:00:00Z","stage":"premise","action":"select","chosen":"dashang-logline-03","alternatives":["…"],"reason":"引擎能自产 30 个转折","persona":"爽感派","model":"agent"}
```

action 取值：`select`（选中）/ `revise`（修改后选中）/ `regenerate`（重生成）/ `reject`（否决）/ `approve`（批准进下一阶段）/ `force_pass`（带理由强放行）。

**后续阶段生成时必须读取决策日志，尊重已有选择，不推翻。**

## 5. 可见性规则（防剧透）

1. `visible_from`：设定/人物卡从指定集起才可注入上下文，之前完全不给模型看。
2. `must_not_know`：角色知识硬约束，写进演员层提示。
3. `hidden`（information_delta）：仅评审和导演层可见，演员层不可见。
4. 伏笔 `planned_payoff` 之前，回收相关细节不进任何生成上下文。

## 6. 版本约定

- 产物不可变：修改 = 生成 v2，YAML 里 `version` 字段 +1，旧内容记入 decisions.jsonl 的 reason。
- state.yaml 每集一份，不覆盖历史。
