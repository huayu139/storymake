# S3 关系 Relationship Web

## LLM 角色：社会网络设计师

关系不是"认识"，是**张力**。每条关系必须能在某一集翻脸或变质。

## 输入

- bible/characters/*.yaml（3 份以上人物卡）
- bible/premise.md（引擎决定关系的走向）

## 产出：bible/relations.yaml（关系边数组）

每条边按 data-model.md 的 relation schema，五个必填要素：

| 字段 | 含义 |
|------|------|
| power_diff | 权力差谁占优（资源/信息/道德/情感） |
| dependency | 谁需要谁、需要什么 |
| unsaid | 没说出口的那句话（信息差的来源） |
| tension | 这段关系的日常张力形态 |
| flip_episode | 预计翻脸/反转集 |

## 生成规则

1. **三张人物卡两两之间至少一条边**（三角关系是短剧的基本盘）
2. 每条关系的 power_diff 必须**不对称**（对称=无张力）
3. unsaid 是核心：至少一条边的 unsaid 与 premise 的引擎直接相关
4. flip_episode 分布要错开，不许集中在同一集
5. 主角与对手的边必须零和（呼应 S2）

## 用户决策点

展示关系网（文字矩阵或简单列表），标注：

- 每条边的张力点
- 每条边的预计翻脸集

用户可：确认 / 改 unsaid / 调 flip_episode / 增删边。

确认后写入 `bible/relations.yaml`，decisions.jsonl 留痕。

## 校验与推进

- `validate.py <slug> --stage relations`（检查两两有边、power_diff 非空、unsaid 非空）
- 请批准 → S4

## 与 S4 的衔接

relations.yaml 中的 flip_episode 会约束 S4 的钉死集位置：翻脸集必须落在某个乐章的转折点上，不允许落在乐章中段无铺垫处。
