# Story Lab 创作工作台 · 计划书

> 本文件是唯一进度权威。每完成一步立即更新"进度追踪"表；偏离计划时先改本文件再继续。
> 最后更新：2026-11-12（C10 v2 场景视觉与提示词层：调研→设计→锚点库→结构字段→8 标签→prompt.py 导出器→e01–e10 全量回填；W5.2b 分镜表未开始）

## 1. 一句话定位

一个**本地优先、文件为源、AI 给选项、人做选择**的长连载故事创作工作台：以 OpenCode skill 形态承载编排与交互，以确定性脚本承载校验，以 Markdown/YAML 文件承载记忆。

## 2. 形态决策（已确认）

- **采用 skill 方案**（替代原 TypeScript CLI 计划）：执行 skill 的 agent 即模型，无需 API Key、无需 LLM 适配层。
- **保留两块代码**：`scripts/validate.py` 确定性校验（硬闸门）、`evals/` 回归用例（防 skill 指令漂移）。
- **数据模型、状态机、决策日志等设计全部沿用既定方案**：变的只是编排层由 engine+cli 换成 skill+对话。

## 3. 架构总览

```
对话层    人与 agent 交互：选/改/重生成/批准
编排层    SKILL.md（主工作流）+ references/stage-*.md（每阶段指令）
能力层    执行 skill 的大模型（发散器/访谈者/导演/演员/编辑，分角色提示）
校验层    scripts/validate.py —— 价值翻转、连续性、schema、伏笔时序（硬闸门）
存储层    projects/<slug>/ 文件为源：bible/ structure/ episodes/ decisions.jsonl
回归层    evals/ 陷阱用例 —— 改 skill 后必跑
```

三条铁律：
1. 文件是唯一事实源，任何状态可从磁盘重建；
2. 模型不记忆，记忆 = 文件 + 决策日志 + 按需读取；
3. 模型生成 → 脚本把关 → 人裁决，三者不互相越位。

## 4. 故事创作层核心内容（必须融入 skill）

这是本项目的灵魂，来自前期调研总结，逐条落位：

| # | 创作方法论 | 落位文件 |
|---|-----------|----------|
| 1 | 7 类决策层：立意/世界/人物/关系/结构/场景/主题 | references/stage-*.md 各阶段 |
| 2 | 大模型分角色：发散器/约束求解器/访谈者/导演/演员/编辑 | 各 stage 文件的"LLM 角色"小节 |
| 3 | Sudowrite：先建 Story Bible 再写正文，上下文是项目资产 | SKILL.md 工作流 + bible/ 目录 |
| 4 | NovelCrafter：Codex 记录"变化"而非"设定"，角色访谈校准声音 | stage-character.md（progressions + 访谈法） |
| 5 | 马良写作：三级大纲 + 上下文装配 + 可见性（防剧透权限） | data-model.md 的 visible_from 字段 |
| 6 | 雪花法：每层只扩一倍，始终可回退 | 状态机 + 版本不可变 |
| 7 | Story Grid：五 commandment + 价值翻转（无翻转即废戏） | stage-card.md + validate.py 硬校验 |
| 8 | IBSEN：导演控剧情、演员演角色，两层分离 | stage-script.md 导演-演员双 prompt |
| 9 | 同质化对策：人格轮换/桥段黑名单/约束随机化/语义距离 | config/personas.json + cliches.json |
| 10 | 信息隔离：角色知识状态 knows/believes/suspects/must_not_know | stage-script.md + state.yaml + 校验 |
| 11 | 决策日志：每次人选了什么、为什么，后续必须尊重 | decisions.jsonl（追加式） |
| 12 | 8 维评审 rubric，分数必须引用原文证据 | stage-review.md + validate.py |
| 13 | 钩子工程：前 5 秒钩子 / 60% 转折 / 末 5 秒悬念，四类悬念轮换 | stage-structure.md + 校验 |
| 14 | 多候选 + 全新上下文 subagent 评审（避免自偏好） | SKILL.md 评审环节 |

## 5. 仓库结构

```
/workspace/storymake/
├── PLAN.md                     ← 本文件（进度权威）
├── docs/architecture.md        ← 架构说明
├── docs/deliverables.md        ← 交付件与外部系统集成说明
├── docs/codex.md               ← 在 Codex 中使用本项目的说明
├── docs/w52-storyboard.md      ← W5.2 场景视觉层/分镜/导出/可写设计
├── docs/scene-prompt-design.md ← C10 v2 调研结论 + 场景提示词构建思路与 QC 规则
├── .opencode/skill/story-workbench/
│   ├── SKILL.md                ← 主工作流与闸门规则
│   ├── references/
│   │   ├── data-model.md       ← 文件结构 + YAML schema + 可见性
│   │   ├── stage-premise.md    ← S1 立意 Premise Lab
│   │   ├── stage-character.md  ← S2 人物 Character Room
│   │   ├── stage-relation.md   ← S3 关系 Relationship Web
│   │   ├── stage-structure.md  ← S4 结构 Story Grid
│   │   ├── stage-card.md       ← S5 场景 Scene Forge
│   │   ├── stage-script.md     ← S6 对白 Director-Actor
│   │   ├── stage-review.md     ← S7 评审 Critic
│   │   └── continuity-rules.md ← 连续性规则（人机共同参照）
│   ├── templates/              ← YAML 模板（生成时照此填写）
│   ├── scripts/validate.py     ← 确定性校验（硬闸门）
│   ├── scripts/webview.py      ← 只读 Web 查看器（HTTP + JSON API）
│   ├── web/                    ← 零依赖前端（index.html/app.js/style.css）
│   └── config/
│       ├── cliches.json        ← 桥段黑名单
│       └── personas.json       ← 5 种创作人格
├── projects/<slug>/            ← 故事项目（文件为源）
├── evals/                      ← 陷阱用例 + 回归脚本
└── AGENTS.md                   ← 项目约束
```

## 6. 项目文件结构（每个故事）

```
projects/<slug>/
├── project.yaml          # 题材、平台、集数、单集秒数、受众、禁忌
├── decisions.jsonl       # 决策日志（追加式，人的每次选择）
├── bible/
│   ├── premise.md        # logline + 引擎 + 选择理由
│   ├── characters/*.yaml # 人物卡（含 progressions 时间线状态）
│   ├── relations.yaml    # 关系网
│   ├── world.md          # 世界规则
│   └── voice.md          # 文风、声音规则、禁用词
├── structure/
│   ├── movements.yaml    # 五乐章 + 4 个钉死集
│   ├── hooks.yaml        # 分集钩子表
│   └── threads.yaml      # 伏笔账本
├── episodes/eNN/
│   ├── cards.yaml        # 场景卡
│   ├── script.md         # 剧本正文
│   ├── state.yaml        # 集末状态 + 各角色知识状态
│   └── review.yaml       # 评审
└── exports/
```

## 7. 里程碑与验收

| 阶段 | 内容 | 验收标准 | 状态 |
|------|------|----------|------|
| W0 | skill 骨架 + data-model + 模板 + validate.py + config + evals | `validate.py` 能检出故意埋的陷阱；skill 可被触发 | ✅ 完成（2026-11-04，evals 15/15 全绿） |
| W1 | 立意 + 人物 + 关系三阶段指令 | 对话走完产出 10 个 logline、3 份人物卡、关系网，全过校验 | ✅ 完成（10 个 logline 收敛 3 个→用户选 A；5 份人物卡；9 条关系边） |
| W2 | 结构阶段（五乐章 + 钉死集 + 钩子表 + 伏笔账本） | 每集结尾留问题；悬念类型轮换；伏笔时序合法 | ✅ 完成（70 集钩子表四类轮换零相邻重复；11 条伏笔全合法） |
| W3 | 场景卡 + 导演-演员剧本 + subagent 评审 | 1 集完整剧本；8 维评分带证据；价值翻转与信息隔离生效 | ✅ e01/e02 完成（e01 round1 独立评审 30/32 → 修复 → round2 32/32 自评；e02 round1 独立评审 29/32 → 修复 → round2 独立复评 33/32 approved）；e03 剧本+两轮评审完成（round1 29/32 → 修复 → round2 32/32 approved，0 blocker），待用户最终验收 |
| W3.5 | 状态看板 skill 能力 | 用户问进度时，一条命令汇总全季进度/伏笔/人物/评审；回归全绿 | ✅ 完成（status.py + stage-status.md + SKILL.md 触发规则；新增 4 条回归，19/19 全绿） |
| W3.6 | 项目总览文件 | 每个项目根目录有 PROJECT.md，阶段/集完成后自动刷新；不开 agent 也能看目标/计划/进度 | ✅ 完成（overview.py + status.py --write 同步；PROJECT.md 含目标/五乐章/接下来 3 集/质量风险/文件导航；evals 31/31 全绿） |
| W4 | 连续性 + 集末状态账本 + 10 集试播 + evals 全绿 | 通读无阻断矛盾；陷阱用例 100% 检出 | ✅ 完成：`continuity.py` + `stage-continuity.md`（K1–K8）；evals 29/29；10 集试播 10/10（e01–e10，continuity 0 BLOCKER/0 WARN）；e08/e09 为 31/32 force_pass，e03 最终验收与 e01 独立复评待用户确认 |
| W5.1 | Web 只读查看器（MVP） | 浏览器可看总览/分集/单集详情；只读，不改事实源 | ✅ 完成（2026-11-10，`webview.py` + `web/`；7 个 API 端点与 7 个视图，绑定 0.0.0.0:8765） |
| W5.2 | 场景视觉层 · 分镜 · 导出 · 可写（立项） | 设计文档落地，四个子阶段可独立验收 | 🚧 立项完成（2026-11-11，`docs/w52-storyboard.md`；实施未开始） |
| W5.2a | 场景视觉层：cards 增 `scene_description`/`props`/`visual_beats`，剧本每场加`【场景】`；人物形象四件套与`【人物】`行（C11/W10）。**v2 扩展（2026-11-12）**：`bible/scenes.yaml` 场景锚点库 + 卡片结构字段 `scene_ref`/`shot_size`/`camera`/`lighting`/`palette` + 剧本 8 标签 + 模糊词黑名单 + `prompt.py` 提示词导出器（C10 v2） | e01 回填后 cards/script 校验 0 blocker；新增 evals 全绿；剧本每场有可拍场景描述；任一集可导出可粘贴生图/生视频提示词 | ✅ 完成（2026-11-12，C10/C11/W10 硬闸门 + C10 v2；e01–e10 全量回填 0 blocker；evals 93/93 全绿） |
| W5.2b | 分镜表 `episodes/eNN/shots.yaml` + S6.5 指令 + `--stage shots` 校验 | e01 分镜通过校验；总时长 72–108s；每个 visual_beat 有镜头覆盖 | 未开始 |
| W5.2c | 导出器 `export.py`：拍摄稿/分镜 CSV/道具清单 | 三种格式导出成功；CSV 表头固定、可被表格软件打开 | 未开始 |
| W5.2d | 受限可写操作（批注/卡片字段/决策日志） | 备份+校验+回滚；越权写被拒；Web 默认只读 | 未开始 |

**第一版可演示目标**：对话从零走到一集完整剧本，产出 5 类文件 + 决策日志 + 评审报告，全部通过 validate.py。

## 8. 进度追踪（及时更新）

| 日期 | 事件 |
|------|------|
| 2026-11-03 | 计划书建立，形态确认为 skill 方案，W0 启动 |
| 2026-11-04 | W0 完成：SKILL.md + 9 个 references + 7 个模板 + validate.py（C1-C8/W1-W7）+ 双配置 + evals；回归 15/15 全绿；中途修复 evals 括号错误与 fixture never_say 不合规两处问题 |
| 2026-11-04 | W1 完成：立意《一秤定乾坤》→ 5 份人物卡 → 9 条关系边，全过校验 |
| 2026-11-04 | W2 完成：70 集五乐章+4 钉死集+钩子表+11 条伏笔账本，全过校验；顺带修复 W1 误报（改按已写集数判断） |
| 2026-11-04 | W3 e01 完成：2 张场景卡→剧本→独立评审 30/32→修复→round2 32/32 approved；round2 因 subagent 免费额度耗尽改为自评并标注 |
| 2026-11-04 | W3 e02 完成：独立评审 29/32（补积分制度前提、老周土办法还手、清 state）→修复→独立复评 33/32 approved；同步修正 e01 open_threads 提前挂账、cards 黄会长信息差、threads t-02 软前置备注 |
| 2026-11-05 | 新增状态看板 skill 能力：scripts/status.py（只读汇总 70 集进度/伏笔/人物/评审/数据健康）+ references/stage-status.md + SKILL.md 触发规则；`--write` 生成 STATUS.md；evals 19/19 全绿 |
| 2026-11-05 | e03 剧本+评审完成：场景卡校验通过 → 剧本 474 字≈105.3s → round1 独立评审 29/32 needs_revision（黑车逻辑/情绪回报/声音扁平）→ 按 fix_top3 修复 → round2 独立复评 32/32 approved，0 blocker；待用户最终验收 |
| 2026-11-05 | W4 启动：新增 `continuity.py`（K1–K8 跨集巡检 + 集末状态账本 + `CONTINUITY.md`）与 `stage-continuity.md`；evals 增至 29/29；e01–e03 巡检 0 BLOCKER，10 集试播进度 3/10 |
| 2026-11-05 | W4 试播完成 e04–e10：7 集场景卡/剧本/state 全过 validate（0 blocker/0 warn）；独立 Critic 至 round3，e04/e05/e07/e10 32/32 approved，e08/e09 31/32 force_pass（0 blocker，理由见 decisions.jsonl）；continuity 0 BLOCKER/0 WARN；试播进度 10/10 |
| 2026-11-05 | 账本同步：threads 新增 t-12（红线图→e16）、t-13（代签笔迹→e11），e08/e09/e10 open_threads 同步；STATUS.md / CONTINUITY.md 刷新；e08 cliffhanger_type 由“闯入”改“反转” |
| 2026-11-06 | 新增项目总览能力：`scripts/overview.py` 生成 `PROJECT.md`（目标/五乐章/接下来 3 集/当前进度/最近完成/故事状态/质量风险/文件导航/最近决策）；`status.py --write` 同步刷新；SKILL.md 要求每阶段/每集完成后自动刷新；evals 增至 31/31 全绿 |
| 2026-11-10 | W5.1 完成：新增 `scripts/webview.py`（Python 标准库只读 HTTP 服务，复用 status.py/continuity.py）+ `web/` 零依赖前端；7 个 API 端点，总览/分集/单集/圣经/结构/连续性/决策 7 个视图；默认 0.0.0.0:8765 |
| 2026-11-10 | 新增 `docs/deliverables.md`：面向外部系统的交付件清单、字段契约、三种集成方式、Web API、兼容约定与消费前自检 |
| 2026-11-10 | 新增 Codex 支持：`.agents/skills/story-workbench` 软链到 `.opencode/skill/story-workbench`；`docs/codex.md` + `AGENTS.md` Codex 小节 |
| 2026-11-11 | W5.2 立项：新增 `docs/w52-storyboard.md`，拆为 W5.2a 场景视觉层 / W5.2b 分镜表 / W5.2c 导出器 / W5.2d 受限可写；确认现有剧本为对白演出稿，场景细节需由 cards 视觉字段 + world.md 注入 + shots.yaml 承载 |
| 2026-11-12 | QC 硬闸门 C10/C11/W10 落地（用户拍板：全 BLOCKER、全量回填 e01–e10、人物首次出场写一行）：validate.py 新增 `_check_visual_qc`/`performance_text`（描述块不计时长，status/continuity 同步），规则文档与模板同步，5 张人物卡补形象四件套+aliases，e01–e10 cards/script 全量回填，全部 0 blocker；evals 31/31 → 59/59 全绿；continuity 0/0；e02 刘婶 W10-name 留待补人物卡 |
| 2026-11-12 | C10 v2 场景视觉与提示词层（用户拍板：全套实施 / 新建 `bible/scenes.yaml` / 剧本 8 标签）：上网调研万相·可灵·Seedance·Sora 官方提示词公式后落 `docs/scene-prompt-design.md`；新增场景锚点库（10 常市场景，空间/光线基调/固定色板/环境音/竖屏构图）、`config/fuzzy-words.json` 模糊词黑名单、`scripts/prompt.py` 提示词导出器（锚点+卡片字段+人物四件套 → 生图/生视频提示词，红线字段结构性排除）；validate.py 升级 C10 v2（锚点引用、景别/机位枚举、光线含光+软硬、palette 含锚点固定色、模糊词、剧本 8 标签）；e01–e10 20 场卡与 20 行【场景】全量回填，cards/script 0 blocker，continuity 0/0，evals 59/59 → 93/93 全绿 |
| 2026-11-12 | 遗留补齐：新建刘婶（liu-shen）、阿贵（a-gui）人物卡（五件套+形象四件套+voice_samples/never_say+aliases），e02/e04/e05 剧本补【人物】行与在场行（e04 两场、e05 场1 加阿贵），relations 补 zhou-liping→a-gui/liu-shen 两条边消 C8；`performance_text()` 三脚本（validate/status/continuity）扣除在场行，evals 新增「在场行不计时长」用例 → 94/94 全绿；e01 独立复评 33/32 approved、e03 最终验收 34/32 approved（均全新上下文 Critic，0 blocker，warning 入 optional_polish 不改剧本），decisions.jsonl 补两条留痕；e08/e09 force_pass 留痕核对无需补；e01–e10 cards/script/review 全 0 blocker，continuity 0/0 |

## 9. 风险与对策

| 风险 | 对策 |
|------|------|
| skill 指令遵循度漂移 | validate.py 硬闸门 + evals 回归 + SKILL.md 禁令 |
| 每次会话重读文件 token 偏高 | index/摘要入口，只深读相关文件 |
| 批量生产效率低 | schema 不变，后续可包成 CLI 迁移 |
| 校验规则被钻空子 | 陷阱用例持续补充，规则以代码固化 |
