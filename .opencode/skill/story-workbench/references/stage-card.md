# S5 场景 Scene Forge

## LLM 角色：导演（约束求解器）

场景卡是生成剧本的**合同**：模型写剧本时不需要猜"这场戏要干嘛"，只需把合同执行得好看。

## 输入

- structure/hooks.yaml 中本集的钩子（question_raised / question_left_open / value 翻转）
- 本集上一集的 state.yaml（人物在哪、知道什么、持有什么）
- 相关人物卡与关系边
- 决策日志

## 产出：episodes/eNN/cards.yaml（场景卡数组，每集 1~3 张）

按 data-model.md 的 scene card schema。**每张卡的五要素**：

### 1. 价值翻转（Story Grid 五 commandment）

每场戏内部按五步走：

1. **Inciting Incident**：打破平衡
2. **Turning Point**：原有策略失效
3. **Crisis**：二选一的困境
4. **Climax**：角色做出选择
5. **Resolution**：选择带来代价

卡上体现为：

- `value_before → value_after`：**必须不同**（相同=废戏，校验器打回）
- `turn`：本场的转折一句话
- 价值词从题材价值表选（都市逆袭：控制/筹码/尊严/信任；甜宠：亲近/疏离/心动/心死…）

### 2. 信息差（information_delta）

四栏必填：

- 每个在场角色 `knows/believes/suspects` 的变化
- `audience`：观众比角色多知道什么
- `hidden`：谁都不知道的（导演与评审可见，演员层不可见）

### 3. must_happen / must_not_happen

- must_happen：本场必须发生的 2~3 件具体事（不是"推进剧情"这种空话）
- must_not_happen：硬边界（不许揭露 X、不许肢体冲突、不许角色说出某秘密）

### 4. 可拍性约束

- 一集一个主场景（短剧基本盘），2~3 个角色
- 预估时长 ≤ project.yaml 的 seconds_per_episode
- `cliffhanger_type` 仅本集最后一场必填，且必须与 hooks.yaml 本集一致

### 5. 因果链

每场必须能写成"**因为 X，所以 Y，但是 Z**"。只有"然后……然后……"的场景直接打回。

## 生成步骤

1. 读本集钩子，确定本集价值翻转的起点与终点
2. 把钩子拆成 1~3 个场景，分配价值翻转（每场一个，不许两个场共享）
3. 填信息差、must/must_not、turn
4. 展示给用户（按卡逐张展示，标注它服务哪个钩子）

## 用户决策点

确认 / 改写某张卡 / 增删场景 / 重生成某张卡（换角度）。

确认后写 cards.yaml，decisions.jsonl 留痕，`validate.py <slug> --stage cards --episode N`（校验价值翻转、角色 id 存在、cast 不超人、时长估算）→ 请批准 → S6。
