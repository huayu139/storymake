# Story Lab 架构说明

> 对应计划书 PLAN.md 第 3 节，实现以本文件为准。

## 1. 分层

```
对话层    人与 agent：选/改/重生成/批准
编排层    SKILL.md（主工作流+闸门） + references/stage-*.md（每阶段指令）
能力层    执行 skill 的大模型（按阶段切换角色：发散器/访谈者/结构师/导演/演员/编辑）
校验层    scripts/validate.py —— 确定性硬闸门（C*=阻断, W*=警告）
观测层    scripts/status.py —— 只读状态看板（进度/伏笔/人物/评审）
对账层    scripts/continuity.py —— 跨集连续性巡检（K1–K8）
存储层    projects/<slug>/ 文件为源（Markdown+YAML+JSONL）
回归层    evals/run_evals.py —— 改 skill 后必跑
```

依赖方向：对话层 → 编排层 → 能力层/校验层 → 存储层。校验层与能力层互不依赖。

## 7. 铁律

1. **文件是唯一事实源**：状态可从磁盘重建，对话记忆不算数。
2. **模型不记忆**：记忆 = 文件 + decisions.jsonl + 按需读取（ContextPackager 的职责由编排层按 data-model.md 的可见性规则执行）。
3. **模型生成 → 脚本把关 → 人裁决**：三者不互相越位；模型自查不算闸门。
4. **跨集必须对账**：每集/每批次跑 `continuity.py`，价值线、位置、道具、伏笔四本账要接得上。

## 3. 数据流（一个阶段的标准循环）

```
读上阶段产物 + 决策日志
  → 按可见性装配上下文（不给未解锁的秘密）
  → 按 stage-*.md 的角色设定生成候选
  → 对话展示，人选/改/重生成（重生成必须换人格或加约束）
  → 写产物 + 追加 decisions.jsonl
  → validate.py（blocker 必须清零）
  → status.py --write（可选：刷新 STATUS.md 快照）
  → 人批准 → 下一阶段
```

评审阶段特殊：用全新上下文 subagent 当 Critic，避免自偏好。

## 4. 阶段状态机

```
S1 立意 → S2 人物 → S3 关系 → S4 结构 →（每集）S5 场景卡 → S6 剧本 → S7 评审 → 下一集
         每阶段: generated → validated → approved（不可跳过，见 data-model.md §2 判据）
```

产物不可变：修改 = version+1 + decisions.jsonl 记录理由。

## 5. 故事创作方法论落位

| 机制 | 实现 |
|------|------|
| 7 类决策分阶段 | references/stage-*.md 各司其职 |
| Story Grid 价值翻转 | 场景卡 value_before≠value_after，validate.py C3 硬校验 |
| IBSEN 导演-演员分离 | stage-script.md 两层生成，演员层信息隔离 |
| 信息隔离防剧透 | state.yaml 的 knows/must_not_know + visible_from，validate.py C4/C5 |
| NovelCrafter progressions | character.yaml 的 progressions 时间线状态 |
| 马良可见性 | visible_from + threads 的 planned_payoff 前不注入 |
| 雪花法可回退 | 分阶段闸门 + 产物不可变 |
| 多样性对抗同质化 | personas.json 轮换 + cliches.json 黑名单 + 候选强制差异化 |
| 决策累积 | decisions.jsonl 追加式，后续阶段必须读取尊重 |
| 钩子工程 | hooks.yaml 三段式 + 四类悬念轮换，validate.py C6 |

## 6. 校验规则索引

- **C1** 死人/退场出场（除非 flashback）
- **C2** 先回收后埋 / dropped 无理由
- **C3** 价值无翻转（场级与集级）
- **C4** must_not_know/hidden 字面泄露进剧本
- **C5** visible_from 未解锁即出场
- **C6** 钩子缺失 / 相邻悬念重复 / 末场悬念与钩子表不一致
- **C7** 必填字段缺失（人物/卡片/评审证据）
- **C8** 关系字段缺失 / power_diff 对称 / 人物无关系边
- **W1-W7** 伏笔超期、悬念单一、AI 味、黑名单、时长偏差、状态突变、决策未尊重

完整描述见 references/continuity-rules.md。

## 7. 演进路径

- W0-W4（当前）：skill 形态，人机对话推进。
- 后续批量需求：同一套 schema 包 CLI，skill 阶段产物直接复用。
- 分镜/视频：新增 stage + 模板 + 校验规则，存储层不动。
