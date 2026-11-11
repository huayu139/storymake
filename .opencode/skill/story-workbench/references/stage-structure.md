# S4 结构 Story Grid

## LLM 角色：结构师（约束求解器）

这一阶段不是发散，是**在约束内求解**：五乐章、钉死集、关系翻脸点、伏笔时序，全部要咬合。

## 输入

- bible/premise.md（引擎）
- bible/characters/*.yaml（弧线）
- bible/relations.yaml（flip_episode 约束）
- project.yaml（episodes 总数）

## 产出三个文件

### 1. structure/movements.yaml —— 五乐章

```yaml
movements:
  - id: 1
    name: 铺垫
    episodes: [1, 2]
    goal: 建立常态与裂缝
  - id: 2
    name: 升级
    episodes: [3, 4]
    goal: 主角主动出击，代价升级
  - id: 3
    name: 付费卡点/中点
    episodes: [5, 6]
    goal: 真相翻转，主角失去依靠
  - id: 4
    name: 一无所有
    episodes: [7, 8]
    goal: 最低点，谎言被戳穿
  - id: 5
    name: 对决与兑现
    episodes: [9, 10]
    goal: 引擎的最终兑现，情感闭环
pinned_episodes:               # 4 个钉死集（10 集季）
  - { episode: 5, kind: 付费卡点 }
  - { episode: 6, kind: 中点 }
  - { episode: 8, kind: 一无所有 }
  - { episode: 10, kind: 大结局 }
```

（集数按 project.yaml 的 episodes 等比调整；乐章边界可微调但四类钉死集必须存在且位置合理。）

### 2. structure/hooks.yaml —— 分集钩子表

每集一条，按 data-model.md 的 hook schema：

- `question_raised`：本集提出的新问题
- `question_left_open`：**必填**，本集结尾必须留给观众的问题（没有就是废集）
- `cliffhanger_type`：揭露 / 反转 / 倒计时 / 闯入 四选一，**相邻集不得重复**，四类在季内都要出现
- `value_before → value_after`：本集的价值翻转（信任→怀疑、安全→危险…）
- `pinned`：与 movements.yaml 的 pinned_episodes 一致

**单集三段式**（写进每集的备注）：前 5 秒钩子 → 约 60% 处转折 → 最后 5 秒悬念。

### 3. structure/threads.yaml —— 伏笔账本

每条伏笔按 thread schema：

- `planted_at` < `planned_payoff`（禁止先回收后埋）
- 付费卡点（如 e05）至少埋 1 条在 e01-e04 的伏笔在此回收
- 大结局前，所有 `status=planted` 的主线伏笔必须安排回收集
- 状态流转：planted → building → paid / dropped（dropped 必须写理由）

## 生成步骤

1. 按 relations.yaml 的 flip_episode 校验乐章边界是否咬合（翻脸点必须在乐章转折处）
2. 排布钉死集 → 填五乐章 → 逐集写钩子 → 排伏笔时序
3. 自检：悬念类型轮换表、每集 question_left_open 非空、伏笔时序合法
4. 展示给用户：乐章表 + 10 集钩子表（表格）+ 伏笔账本（表格）

## 用户决策点

- 调整某集的悬念类型/留的问题
- 改钉死集位置
- 增删伏笔
- 要求重排（换一种乐章切法）

确认后写三个文件，decisions.jsonl 留痕，`validate.py <slug> --stage structure` 全过后请批准 → S5。
