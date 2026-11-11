# 连续性规则（人机共同参照）

这些规则由 `validate.py` 硬校验，同时供创作时自查。**模型自查不是闸门，脚本才是。**

## 一、阻断级（BLOCKER，必须修复才能推进）

### C1 死人/退场人物出场
`state.yaml` 中标记 `dead: true` 或 `written_out: true` 的角色，不得出现在后续集的 cards.yaml cast 或 script.md 对话中。
（处理方式：闪回需在卡上标 `flashback: true` 并注明时间点。）

### C2 先回收后埋
thread 的 `planted_at >= planned_payoff` 即违规。回收必须发生在埋设之后。

### C3 价值无翻转
场景卡 `value_before == value_after` → 废戏，打回重写。

### C4 信息泄露（剧透）
剧本台词或 must_happen 中出现该角色 `must_not_know` 的内容 → 必须重写该场。
（`hidden` 内容只有导演层/评审层可见，演员层出现即违规。）

### C5 未解锁即可见
设定/人物卡的 `visible_from > 当前集数`，却已出现在当前集上下文产物中 → 违规。

### C6 钩子缺失
- hooks.yaml 某集 `question_left_open` 为空
- 本集剧本结尾没有留下该问题
- 相邻两集 `cliffhanger_type` 相同

### C7 人物字段缺失
character.yaml 缺 want/fear/secret/lie/wound/voice_samples（少于 3 句）/never_say（少于 2 句）。

### C8 关系字段缺失
relation 缺 power_diff/dependency/unsaid/tension；或 power_diff 写成"均等/对称"。

### C9 状态跳变未记录
人物位置、持有物在相邻集之间无剧本依据地突变（eNN 在车库，eNN+1 无过渡却在家中）→ 至少要有一句交代或记为 warning 由人确认。

## 二、警告级（WARN，需用户知情）

### W1 伏笔超期
`status=planted` 且距 `planted_at` 已过 ≥3 集未推进（未变 building/paid）→ 提醒排回收。

### W2 悬念类型单一
最近 3 集 cliffhanger_type 相同（C6 拦相邻，W1 拦连续 3）。

### W3 角色同质化
三角色 voice_samples 的平均句长/句式结构过于接近 → 建议拉开。

### W4 AI 味词
script.md 命中 config/aiisms 高频词（"眼中闪过一丝""不禁""仿佛在诉说着"等）→ 建议润色。

### W5 桥段黑名单
任意产物命中 config/cliches.json → 提醒确认是否有意为之。

### W6 时长偏差
按中文 4.5 字/秒估算，剧本字数偏离 `seconds_per_episode` ±20%。

### W7 决策未尊重
本阶段产物与 decisions.jsonl 中已 select 的决策冲突且无 `revise` 记录 → 提醒。

## 三、信息隔离速查（生成剧本时贴在演员提示里）

```
你知道：（knows + believes + suspects 的本场部分）
你绝不知道：（must_not_know 全部）——任何台词、动作不得暗示这些
观众知道但你不知道：（audience 栏）—— 不许利用
```

## 四、校验命令

```bash
/workspace/tools/miniconda3/bin/python \
  .opencode/skill/story-workbench/scripts/validate.py <slug> [--stage <阶段>] [--episode N]
```

退出码：0 = 无 blocker（可有 warning）；1 = 存在 blocker。
