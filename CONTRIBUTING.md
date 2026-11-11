# 贡献指南

## 可以贡献什么

- 新增或改进创作阶段规则（`references/`）
- 新增校验规则与回归用例（`scripts/`、`evals/`）
- 修复脚本缺陷
- 改进 Web 看板
- 完善文档

## 开发流程

1. Fork 仓库并新建分支。
2. 修改 `.opencode/skill/story-workbench/` 下的**真实文件**；`.agents/skills/story-workbench` 只是软链，不要单独改。
3. 运行回归：

```bash
python3 -m pip install pyyaml
python3 evals/run_evals.py
```

4. 确保 `31/31 通过` 或更多用例全绿。
5. 提交 PR，说明改了什么、为什么、如何验证。

## 约束

- 所有面向用户的文案与注释使用中文；代码标识符用英文。
- 文件是唯一事实源；不要把状态只存在对话或内存里。
- 校验器与生成逻辑分离：模型生成，脚本把关，人裁决。
- 新增校验规则时，必须同时补正例与反例测试。
- 不要提交 `projects/`、`opencode.json`、密钥、快照或导出产物。

## 提交信息

建议使用：

```text
feat: 新增 xxx 校验
fix: 修复 status.py 在 xxx 下的崩溃
docs: 补充 xxx 说明
test: 增加 xxx 回归用例
```
