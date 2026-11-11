# S7 评审 Critic

## LLM 角色：编辑（判断者，不是创作者）

**必须用全新上下文的 subagent 执行**，不给它看生成过程，只给它产物——避免自己写自己评的自偏好。

## 输入（只给这些，不给生成历史）

- episodes/eNN/script.md
- episodes/eNN/cards.yaml
- episodes/eNN/state.yaml
- bible/characters/*.yaml、relations.yaml
- structure/hooks.yaml（本集行）
- continuity-rules.md

## 8 维评分（每项 1~5 分，每个分数必须引用原文证据）

| 维度 | 看什么 | 5 分标准 |
|------|--------|----------|
| hook 钩子强度 | 前 5 秒是否冲突/异常，能否静音看懂 | 开场即冲突，静音也懂 |
| causality 因果连贯 | 是否"因为 X 所以 Y 但是 Z" | 无流水账，每场有因果链 |
| character_consistency 人物一致性 | 行为是否符合 want/fear/secret | 无 OOC，选择符合五件套 |
| voice_distinctness 声音辨识度 | 遮名能否认出说话人 | 三角色台词风格截然不同 |
| value_shift 价值翻转 | 场景与集级价值是否变化 | 每场 value_before≠value_after 且兑现 |
| information_management 信息管理 | 是否泄底、是否合理利用信息差 | 无 must_not_know 泄露，信息差被主动使用 |
| emotional_payoff 情感兑现 | 铺垫是否有回收、情绪是否到位 | 伏笔按账本推进，情绪有落点 |
| originality 原创性 | 是否撞 cliches.json、是否有 AI 味 | 无黑名单桥段，无重复句式 |

## 产出：episodes/eNN/review.yaml

按 data-model.md 的 review schema：

- `scores`：8 项，每项 `{score, evidence}`，evidence 必须是原文引用
- `issues`：问题清单，每条 `{code, severity, evidence, location}`
  - severity=blocker：信息泄露、人物 OOC、价值无翻转、钩子缺失
  - severity=warning：文风、节奏、轻微重复
- `total`：总分
- `verdict`：total ≥ 阈值（默认 32）且无 blocker → `approved`；否则 `needs_revision`

## 修复循环

```
needs_revision → 提炼"必须修改的 3 处"（按严重度排序）
              → 回 S6 只修这 3 处（不许整篇重写，避免好的部分被冲掉）
              → 再评审（round +1）
              → 最多 3 轮，仍不达标 → 停下，把问题清单交给用户裁决
```

用户可 `force_pass` 强制放行，**必须写理由**并记入 decisions.jsonl。

## 评审后的展示

给用户看：

1. 8 维得分表（附证据）
2. blocker / warning 清单
3. 建议：修复 or 通过

等用户决定。通过后：decisions.jsonl 记 `action=approve`，本集状态完成，进入下一集 S5（或全季完成）。
