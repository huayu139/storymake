# 项目约束

- 所有交流（提问、解释、总结、计划）必须使用中文
- 代码注释也尽量使用中文
- 代码本身、标识符仍使用英文命名规范

## 项目级凭证与迁移

- Git 部署密钥放在 `.keys/`（私钥 `id_ed25519_storymake`、公钥 `.pub`、包装器 `git-ssh.sh`），随项目目录整体迁移。
- `.keys/` 已在 `.gitignore` 中排除，**永不提交**；GitHub 上只登记公钥。
- 推送用 `scripts/push.sh`，或 `GIT_SSH_COMMAND="$PWD/.keys/git-ssh.sh" git push`。
- 换机器：整目录 `rsync`/`tar` 复制，不要只 `git clone`；详见 `.keys/README.md`。

## 在 Codex 中使用

- 本项目是故事创作工作台，Codex 技能位于 `.agents/skills/story-workbench`（软链到 `.opencode/skill/story-workbench`）。
- 创作、续写、评审、查进度时，优先显式调用 `$story-workbench`；先读 `.agents/skills/story-workbench/SKILL.md`。
- 事实源是 `projects/<slug>/` 下的 bible/structure/episodes；`PROJECT.md`、`STATUS.md`、`CONTINUITY.md` 只是快照。
- Python 统一使用 `/workspace/tools/miniconda3/bin/python`（需 PyYAML）。
- 详细用法见 `docs/codex.md`。

## 软件安装

- 所有新安装的软件（含解压的工具、下载的二进制、自编译产物、包管理器安装的依赖）必须安装在 `/workspace/tools/<软件名>/` 下，禁止安装到系统目录（如 /usr、/opt 等）
- 每完成一次安装，须把「软件名称、版本、实际路径」记录到本文件的"已安装软件清单"中
- 系统未安装或需要多版本的工具应优先复用 `/workspace/tools` 下已有的安装（见下方清单），避免重复下载
- 除系统自带的 git 及 `/usr/local/bin/opencode` 外，清单中的软件均不在 PATH 中，使用时需指定完整路径或临时导出 PATH/环境变量

## 已安装软件清单

> 最后核对日期：2026-11-03（已按实际文件系统逐项验证）

### 语言与运行时

| 软件 | 版本 | 路径 |
|------|------|------|
| Node.js | v24.21.0 | `/workspace/tools/node-v24.21.0-linux-x64` |
| Python (Miniconda3) | 3.13.13 | `/workspace/tools/miniconda3/bin/python` |
| Go | 1.27.2 | `/workspace/tools/go` |
| OpenJDK | 21.0.8 LTS | `/workspace/tools/openjdk-21` |
| OpenJDK | 23-valhalla | `/workspace/tools/openjdk-23` |
| OpenJDK | 25 | `/workspace/tools/openjdk-25` |
| Flutter | 3.44.1 stable | `/workspace/tools/flutter` |
| Gradle | 8.10.2 | `/workspace/tools/gradledir/wrapper/dists/gradle-8.10.2-bin/*/gradle-8.10.2` |
| Gradle | 8.13 | `/workspace/tools/gradledir/wrapper/dists/gradle-8.13-bin/*/gradle-8.13` |
| Gradle | 9.0-milestone-1 | `/workspace/tools/gradledir/wrapper/dists/gradle-9.0-milestone-1-bin/*/gradle-9.0-milestone-1` |

### Android / 逆向分析

| 软件 | 版本 | 路径 |
|------|------|------|
| Android SDK | platforms 35/36，build-tools 35.0.0、35.0.1、36.0.0、36.1.0 | `/workspace/tools/androidsdk`（另含 cmake、cmdline-tools、emulator、ndk、platform-tools、system-images 等） |
| scrcpy | 5.0.1 | `/workspace/tools/scrcpy/scrcpy`（同目录附 adb、scrcpy-server） |
| apktool | — | `/workspace/tools/apktool/apktool.jar` |
| smali | — | `/workspace/tools/smali/smali.jar` |
| jadx-headless-mcp | 0.7.1 | `/workspace/tools/jadx-mcp/jadx-headless-mcp-0.7.1-all.jar` |
| Frida Gadget | — | `/workspace/tools/frida-gadget/frida-gadget.so` |

> 注意：`/workspace/tools/frida-venv` 的 Python 解释器指向 `/home/jaskon139/tools/frida-venv/bin/python3.14`，该路径在本机不存在，`frida`、`frida-apk` 等 CLI 目前不可用，需要重建虚拟环境后才能使用。

### 桌面 / GUI 应用

| 软件 | 版本 | 路径 |
|------|------|------|
| Godot | 4.7.2 stable | `/workspace/tools/godot/Godot_v4.7.2-stable_linux.x86_64` |
| Postman | — | `/workspace/tools/Postman/app/Postman` |
| Discord | — | `/workspace/tools/Discord/discord` |
| FileZilla | 3 | `/workspace/tools/FileZilla3/bin/filezilla` |
| Throne | — | `/workspace/tools/Throne/Throne`（同目录含 sing-box 1.15.0-alpha.4 与 ThroneCore） |
| Blender MCP | — | `/workspace/tools/blender_mcp`、`/workspace/tools/blender-mcp-main` |

### 网络工具

| 软件 | 版本 | 路径 |
|------|------|------|
| Speedtest (Ookla) | 1.2.0.84 | `/workspace/tools/speedtest/speedtest` |
| CloudflareSpeedTest | — | `/workspace/tools/cfst_test/cfst` |
| aggtunnel | — | `/workspace/tools/aggtunnel/`（agg-tunnel、agg-speed） |
| gotty-client | 1.6.1 | `/workspace/tools/gotty-client_Linux_x86_64/gotty-client_1.6.1_linux_amd64` |
| sing-box | 1.15.0-alpha.4 | `/workspace/tools/Throne/sing-box-1.15.0-alpha.4-linux-amd64/sing-box` |
| sing-box 配置 | — | `/workspace/tools/sing-box/`（仅有配置文件 `configcloduflare.json`） |
| OpenVPN / v2ray 配置 | — | `/workspace/tools/openvpn/`（`one.ovpn` 及节点配置） |

### 嵌入式 / 浏览器 / 其他

| 软件 | 版本 | 路径 |
|------|------|------|
| SDCC ucsim 模拟器 | — | `/workspace/tools/sdcc-ucsim/usr/bin/`（ucsim_51、ucsim_z80 等） |
| SDCC 工具链 | — | `/workspace/tools/sdcc/usr/bin/`（sdcc、sdas8051 等） |
| Playwright 浏览器 | chromium-1248 | `/workspace/tools/ms-playwright/`（含 chromium、chromium_headless_shell、ffmpeg-1013） |
| FFmpeg | N-128212（2026-10-30） | `/workspace/tools/ffmpeg/bin/ffmpeg`、`/workspace/tools/ffmpeg/bin/ffprobe` |
| OpenCode | v2.2.5 | `/workspace/tools/opencode/opencode`（另有 `/usr/local/bin/opencode` 可直接调用） |
| wifibat | — | `/workspace/tools/wifibat`（v2ray、ovpn 等代理配置集合） |
| 字体资源 | — | `/workspace/tools/fonts/` |
| 依赖库 | — | `/workspace/tools/chromium-deps`、`/workspace/tools/libxcb1`（chromium 相关依赖） |
| 容器启动脚本 | — | `/workspace/tools/dockerfile/`（antigravity_run.sh、opencode_run.sh 等；仅为脚本，Antigravity 本体未安装） |

## 核对说明

本次核对移除了以下与实际不符的条目，勿再按旧记录查找：

- `Node.js v24.10.0`：目录不存在
- `Antigravity`：仅存在 `/workspace/tools/dockerfile/antigravity_run.sh` 启动脚本，本体未安装
- `搜狗输入法`：`/workspace/tools/sogou` 不存在
- `OnionHop CLI`：全盘未找到对应目录
- `GUI.for.SingBox-linux-amd64`：路径不存在，sing-box 二进制实际位于 Throne 目录
- `/workspace/tools/bin`：目录不存在
- `gotty-client` 原路径有误，已改为实际目录名
