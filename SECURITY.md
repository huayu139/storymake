# 安全策略

## 报告问题

如果发现安全问题，请不要公开提交 Issue。请通过仓库维护者提供的私下渠道联系，并附上：

- 受影响的文件或版本
- 复现步骤
- 可能的影响范围

## 密钥与配置

- 本仓库**不包含**任何 API Key。
- `opencode.json` 已在 `.gitignore` 中排除；请基于 `opencode.example.json` 在本地创建。
- 推荐用环境变量注入密钥，不要把密钥写进配置文件：

```json
{
  "options": {
    "baseURL": "{env:OPENCODE_BASE_URL}",
    "apiKey": "{env:OPENCODE_API_KEY}"
  }
}
```

- 如果密钥曾进入 Git 历史，仅删除文件不够；请立即轮换密钥，并清理历史。

## Web 看板

`webview.py` 是只读服务，没有鉴权。默认只应监听 `127.0.0.1`。如需对外访问，请放在内网或带鉴权的反向代理之后。
