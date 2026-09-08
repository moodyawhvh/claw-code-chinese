<div align="center">

# claw-code 中文文档

**[中文版] claw-code — 由 AI 代理自动打理的 Rust CLI 代理框架"博物馆展品"**

[![原项目](https://img.shields.io/badge/原项目-ultraworkers--claw-code-blue?style=flat-square&logo=github)](https://github.com/ultraworkers/claw-code)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](https://github.com/ultraworkers/claw-code/blob/main/LICENSE)
[![微信联系](https://img.shields.io/badge/微信-uaycar-brightgreen?style=flat-square&logo=wechat)](#)

> 本文档是 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 官方 README 的完整中文翻译。英文项目名、命令与链接保留原样;完整源代码请访问原项目。

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

</div>

---

## 重要说明

**Claw Code 并不是一个严肃的生产级项目。** 这个仓库与其说是产品推介,不如说更像一座博物馆展品:一件由"带钳子的 gajae"们养活的甲壳类文物,由代理负责清扫和贴标签,并依照上游 harness 自动维护。

正如项目哲学中所述,它不打算像普通产品仓库那样靠人手操作。这是一个**代理管理的展品(agent-managed exhibit)**:harness 负责规划、执行、验证、标注和保存这件文物,而"螃蟹们"维持水箱运转。

- 如果你想真正跑点活,请从 [LazyCodex](https://github.com/code-yeongyu/lazycodex) 或 [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code) 开始。
- 如果你只想参观"Claw Code 时刻"这块奇怪的小化石,请继续往下读。
- 项目哲学的更长公开说明见[此处](https://x.com/realsigridjin/status/2039472968624185713)。

## 当前仓库结构

- **`rust/`** — 规范的 Rust 工作区,即 `claw` CLI 二进制所在处
- **`USAGE.md`** — 面向任务的当前产品使用指南
- **`PARITY.md`** — Rust 移植的对照(parity)状态与迁移说明
- **`ROADMAP.md`** — 活跃路线图与清理待办
- **`PHILOSOPHY.md`** — 项目意图与系统设计定位
- **`src/` + `tests/`** — 配套的 Python/参考工作区与审计辅助工具;并非主要运行面

## 快速开始

> [!WARNING]
> **`cargo install claw-code` 装的是错误的东西。** crates.io 上的 `claw-code` crate 是一个已废弃的占位包,只会放置 `claw-code-deprecated.exe` 而不是 `claw`,运行时仅打印 `"claw-code has been renamed to agent-code"`。**不要使用 `cargo install claw-code`。** 要么从本仓库源码构建,要么安装上游二进制:
>
> ```bash
> cargo install agent-code   # 上游二进制 — 安装的是 'agent.exe'(Windows)/ 'agent'(Unix),不是 'agent-code'
> ```
>
> 本仓库(`ultraworkers/claw-code`)**仅支持从源码构建**——请按以下步骤操作。

```bash
# 1. 克隆并构建
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace

# 2. 设置你的 API Key(Anthropic API Key —— 不是 Claude 订阅)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. 验证一切接线正常
./target/debug/claw doctor

# 4. 运行一条提示词
./target/debug/claw prompt "say hello"

# 5. 启动交互式会话
./target/debug/claw
```

> [!NOTE]
> **Windows(PowerShell):** 二进制是 `claw.exe` 而非 `claw`。使用 `.\target\debug\claw.exe`,或运行 `cargo run -- prompt "say hello"` 跳过路径查找。

> [!NOTE]
> **ACP / Zed 状态:** `claw-code` 目前尚未内置 ACP/Zed 守护进程或 JSON-RPC 入口。请运行 `claw acp`(或 `claw --acp`)查看当前状态,不要靠猜源码目录;`claw acp serve` 目前只是一个可发现性别名,返回状态并以退出码 0 结束,真正的 ACP 支持在 `ROADMAP.md` 中单独跟踪。公开 JSON 契约见 `docs/g011-acp-json-rpc-status-contract.md`。

### Windows 安装

**PowerShell 是受支持的 Windows 路径。** 用哪个 shell 都行。Windows 上常见的入门问题是:

1. **先安装 Rust** — 从 <https://rustup.rs/> 下载并运行安装器,完成后关闭并重新打开终端。
2. **确认 Rust 已加入 PATH:**
   ```powershell
   cargo --version
   ```
   如果失败,重新打开终端,或按 Rust 安装器输出提示设置 PATH 后重试。
3. **克隆并构建**(PowerShell、Git Bash 或 WSL 均可):
   ```powershell
   git clone https://github.com/ultraworkers/claw-code
   cd claw-code/rust
   cargo build --workspace
   ```
4. **运行**(PowerShell —— 注意 `.exe` 和反斜杠):
   ```powershell
   $env:ANTHROPIC_API_KEY = "sk-ant-..."
   .\target\debug\claw.exe prompt "say hello"
   ```

关于发布版 ZIP、PATH 设置、Provider 切换和通知冒烟检查,参见原仓库 `docs/windows-install-release.md`。

**Git Bash / WSL** 是可选方案,不是必需品。如果你更喜欢 bash 风格路径(`/c/Users/you/...` 而非 `C:\Users\you\...`),随 Git for Windows 附带的 Git Bash 就很好用。在 Git Bash 中出现 `MINGW64` 提示符是正常现象,不代表安装损坏。

## 构建后:定位二进制并验证

运行 `cargo build --workspace` 后,`claw` 二进制已构建,**但不会**自动安装到系统。以下是它的位置与验证方法。

### 二进制位置

在 `claw-code/rust/` 中执行 `cargo build --workspace` 后:

**Debug 构建(默认,编译更快):**
- **macOS/Linux:** `rust/target/debug/claw`
- **Windows:** `rust/target/debug/claw.exe`

**Release 构建(优化,编译更慢):**
- **macOS/Linux:** `rust/target/release/claw`
- **Windows:** `rust/target/release/claw.exe`

如果运行 `cargo build` 时没加 `--release`,二进制就在 `debug/` 目录里。

### 验证构建成功

直接用完整路径测试二进制:

```bash
# macOS/Linux(debug 构建)
./rust/target/debug/claw --help
./rust/target/debug/claw doctor

# Windows PowerShell(debug 构建)
.\rust\target\debug\claw.exe --help
.\rust\target\debug\claw.exe doctor
```

以下 PowerShell 冒烟命令不需要真实凭据:

```powershell
$env:CLAW_CONFIG_HOME = Join-Path $env:TEMP "claw config home"
New-Item -ItemType Directory -Force -Path $env:CLAW_CONFIG_HOME | Out-Null
Remove-Item Env:\ANTHROPIC_API_KEY, Env:\ANTHROPIC_AUTH_TOKEN, Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue
.\rust\target\debug\claw.exe help
.\rust\target\debug\claw.exe status
.\rust\target\debug\claw.exe config env
.\rust\target\debug\claw.exe doctor
```

这些命令全部成功即说明构建正常。`claw doctor` 是你的第一道健康检查——它会验证 API Key、模型访问与工具配置。

### 可选:加入 PATH

想在任意目录直接运行 `claw`,可任选一种方式:

**方式一:符号链接(macOS/Linux)**
```bash
ln -s $(pwd)/rust/target/debug/claw /usr/local/bin/claw
```
然后重载 shell 并测试:
```bash
claw --help
```

**方式二:使用 `cargo install`(全平台)**

构建并安装到 Cargo 默认位置(`~/.cargo/bin/`,通常已在 PATH 中):
```bash
# 在 claw-code/rust/ 目录下
cargo install --path . --force

# 然后在任意位置
claw --help
```

**方式三:修改 shell 配置(bash/zsh)**

在 `~/.bashrc` 或 `~/.zshrc` 中加入:
```bash
export PATH="$(pwd)/rust/target/debug:$PATH"
```

重载 shell:
```bash
source ~/.bashrc  # 或 source ~/.zshrc
claw --help
```

### 故障排查

- **"command not found: claw"** — 二进制在 `rust/target/debug/claw`,但不在 PATH 上。使用完整路径 `./rust/target/debug/claw`,或按上文做符号链接/安装。
- **"permission denied"** — macOS/Linux 上可能需要 `chmod +x rust/target/debug/claw`(可执行位未设置时,较少见)。
- **Debug 与 Release** — 构建很慢说明你在默认的 debug 模式。给 `cargo build` 加 `--release` 可获得更快的运行时性能,但构建本身需要 5–10 分钟。

> [!NOTE]
> **认证:** claw 需要 **API Key**(`ANTHROPIC_API_KEY`、`OPENAI_API_KEY` 等)——不支持 Claude 订阅登录。

确认二进制可用后,运行工作区测试套件:

```bash
cd rust
cargo test --workspace
```

## 文档地图

- `USAGE.md` — 快捷命令、认证、会话、配置、parity harness
- `docs/navigation-file-context.md` — 终端导航、回滚缓冲、`@path` 文件上下文、附件与密钥安全指引
- `docs/local-openai-compatible-providers.md` — Ollama/llama.cpp/vLLM 配置、Claw 多 Provider 定位与本地 skills 安装检查
- `docs/windows-install-release.md` — PowerShell 优先的安装、发布产物、Provider 切换与 Windows/WSL 通知冒烟路径
- `rust/README.md` — crate 地图、CLI 面、特性、工作区布局
- `PARITY.md` — Rust 移植的对照状态
- `rust/MOCK_PARITY_HARNESS.md` — 确定性 mock 服务 harness 细节
- `ROADMAP.md` — 活跃路线图与待清理工作
- `docs/g004-events-reports-contract.md` — Stream 2 泳道事件/报告契约指引
- `PHILOSOPHY.md` — 项目为何存在以及如何运营
- `CONTRIBUTING.md`、`SECURITY.md`、`SUPPORT.md`、`CODE_OF_CONDUCT.md` — 贡献、漏洞报告、支持与社区政策
- `LICENSE` — 本仓库的 MIT 许可证

*(以上文档均位于[原项目仓库](https://github.com/ultraworkers/claw-code)。)*

## 生态系统

Claw Code 与更庞大的 UltraWorkers 工具链一同公开构建:

- [clawhip](https://github.com/Yeachan-Heo/clawhip)
- [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)
- [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode)
- [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex)
- [gajae-code](https://github.com/Yeachan-Heo/gajae-code)
- [UltraWorkers Discord](https://discord.gg/5TUQKqFWd)

## 归属 / 关联声明

- 本仓库**不**主张对原始 Claude Code 源材料的所有权。
- 本仓库**与 Anthropic 无关联、未获其背书、也非其维护**。

---

## 版权与联系方式

本项目为 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 的中文翻译版本,所有代码版权归原项目作者所有,遵循其原始 MIT 许可证。

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

**如果觉得有用,请给原项目点个 Star!** ⭐
