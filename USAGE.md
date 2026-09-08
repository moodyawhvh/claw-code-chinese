> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。(本文件超过 10000 字符,按预算翻译核心章节,个别超长 JSON 示例有删节,文末有说明。)

# Claw Code 使用指南

本指南覆盖 `rust/` 下当前的 Rust workspace 与 `claw` CLI 二进制。如果你是新手,请把 doctor 健康检查作为第一次运行:启动 `claw`,然后执行 `/doctor`。

## 快速健康检查

在跑 prompt、会话或自动化之前先执行:

```bash
cd rust
cargo build --workspace
./target/debug/claw
# REPL 内的第一条命令
/doctor
```

`/doctor` 是内置的安装与预检诊断。保存过会话后,可以用 `./target/debug/claw --resume latest /doctor` 重新运行。

## 前置条件

- 带 `cargo` 的 Rust 工具链
- 以下任一:
  - `ANTHROPIC_API_KEY`(直连 API)
  - `ANTHROPIC_AUTH_TOKEN`(Bearer token 认证)
- 可选:指向代理或本地服务时设置 `ANTHROPIC_BASE_URL`

## 安装 / 构建 workspace

```bash
cd rust
cargo build --workspace
```

debug 构建完成后,CLI 二进制位于 `rust/target/debug/claw`(Windows 上为 `rust\target\debug\claw.exe`)。构建后的第一步请做上面的 doctor 检查。PowerShell 优先的安装、release ZIP、PATH、provider 切换以及 Windows/WSL 通知示例,见 [`docs/windows-install-release.md`](./docs/windows-install-release.md)。

## 快速上手

### 首次运行的 doctor 检查

```bash
cd rust
./target/debug/claw
/doctor
```

也可以直接以 JSON 输出运行 doctor,便于脚本化:

```bash
cd rust
./target/debug/claw doctor --output-format json
```

**注意:** 诊断类动词(`doctor`、`status`、`sandbox`、`version`)支持 `--output-format json` 以获得机器可读输出。非法后缀参数(如 `--json`)会在解析阶段被拒绝,而不是落回 prompt 分发。
`version --output-format json` 输出结构化的构建来源信息,包括完整 `git_sha`、派生的 `git_sha_short`、`is_dirty`、`branch`、`commit_date`、`commit_timestamp`、`rustc_version`、运行时 `executable_path` 与 `binary_provenance`;JSON 的人类可读报告放在 `human_readable` 字段,不再重复放在 `message` 里。`status --output-format json` 通过 `workspace.memory_files[]` 暴露每个已加载项目记忆文件的 `path`、`source`、`origin`、`scope_path`、`outside_project`、`chars`、`contributes`。

### 初始化仓库

为新仓库生成 `.claw/settings.json`、`.claw.json`、`.gitignore` 条目和 `CLAUDE.md` 指引文件:

```bash
cd /path/to/your/repo
./target/debug/claw init
```

文本模式(人类可读)显示工件创建摘要、项目路径和后续步骤。操作是幂等的——同一仓库多次运行会把已存在的文件标记为 "skipped",缺失子文件被补齐时把 `.claw/` 报为 "partial",`.claw/sessions/` 则推迟到第一次成功保存会话时创建。

脚本化使用 JSON 模式:
```bash
./target/debug/claw init --output-format json
```

返回结构化输出,包含 `project_path`、`created[]`、`updated[]`、`partial[]`、`deferred[]`、`skipped[]` 数组(每种工件状态一个),以及携带每个文件 `name` 与机器稳定 `status` 标签的 `artifacts[]`。旧版 `message` 字段保留以兼容。

**结构化字段的意义:** claw 可以识别每个工件的状态(`created`、`updated`、`partial`、`deferred`、`skipped`),不必对人类可读文本做子串匹配。可基于状态数组写条件化的后续逻辑(例如只有文件确实被创建过才提交,而不只是更新)。

### 交互式 REPL

```bash
cd rust
./target/debug/claw
```

### 单次 prompt

```bash
cd rust
./target/debug/claw prompt "summarize this repository"
```

当自动化流程已经产出 prompt 正文时,可以通过 stdin 管道传入:

```bash
printf 'summarize this repository\n' | ./target/debug/claw prompt --output-format json
```

### 简写 prompt 模式

```bash
cd rust
./target/debug/claw "explain rust/crates/runtime/src/lib.rs"
```

当简写 prompt 本身以 `-` 或 `--` 开头时,使用 POSIX 的 `--` 参数终止符:

```bash
./target/debug/claw -- "-summarize this dash-prefixed text"
```

### 脚本化 JSON 输出

```bash
cd rust
./target/debug/claw --output-format json prompt "status"
```

### 查看 worker 状态

`claw state` 读取 `.claw/worker-state.json`,该文件由交互式 REPL 或单次 prompt 在 worker 执行任务时写入,包含 worker ID、会话引用、模型与权限模式。

前提:你必须先在本仓库运行过一次 `claw`(交互式 REPL)或 `claw prompt <text>`,以生成 worker 状态文件。

```bash
cd rust
./target/debug/claw state
```

JSON 模式:
```bash
./target/debug/claw state --output-format json
```

如果从未有 worker 执行过就运行 `claw state`,会看到带提示的错误:
```
error: no worker state file found at .claw/worker-state.json
  Hint: worker state is written by the interactive REPL or a non-interactive prompt.
  Run:   claw               # start the REPL (writes state on first turn)
  Or:    claw prompt <text> # run one non-interactive turn
  Then rerun: claw state [--output-format json]
```

## 高级斜杠命令(仅限交互式 REPL)

以下命令在交互式 REPL(无参数运行 `claw`)内可用。它们为助手扩展了 workspace 分析、规划与导航能力。

### `/ultraplan` —— 多步推理的深度规划

**用途:** 用扩展推理把复杂任务拆解为步骤。

```bash
# 启动 REPL
claw

# REPL 内
/ultraplan refactor the auth module to use async/await
/ultraplan design a caching layer for database queries
/ultraplan analyze this module for performance bottlenecks
```

输出:带编号步骤的结构化计划,含每步推理与预期结果。想让助手在编码前深入思考问题时使用。

### `/teleport` —— 跳转到文件或符号

**用途:** 按名称快速导航到文件、函数、类或结构体。

```bash
# 跳转到符号
/teleport UserService
/teleport authenticate_user
/teleport RequestHandler

# 跳转到文件
/teleport src/auth.rs
/teleport crates/runtime/lib.rs
/teleport ./ARCHITECTURE.md
```

输出:文件内容,高亮目标符号或整个文件加载。适合不手动翻目录地探索代码库。存在多个匹配时,助手会给出最可能的候选。

### `/bughunter` —— 扫描疑似 bug 与问题

**用途:** 分析代码中的常见陷阱、反模式与潜在 bug。

```bash
# 扫描整个 workspace
/bughunter

# 扫描指定目录或文件
/bughunter src/handlers
/bughunter rust/crates/runtime
/bughunter src/auth.rs
```

输出:可疑模式清单及解释(例如 "unchecked unwrap()"、"potential race condition"、"missing error handling")。每条发现包含文件、行号与建议修复。可作为完整代码评审前的第一遍初筛。

## 模型与权限控制

```bash
cd rust
./target/debug/claw --model sonnet prompt "review this diff"
./target/debug/claw --permission-mode read-only prompt "summarize Cargo.toml"
./target/debug/claw --permission-mode workspace-write prompt "update README.md"
./target/debug/claw --allowedTools read,glob "inspect the runtime crate"
./target/debug/claw --cwd ../other-workspace status --output-format json
```

全局 workspace 覆盖旗标:`--cwd PATH`、`-C PATH`、`--directory PATH`,可放在任意子命令之前。它们在命令分发前校验,优先于进程 `$PWD`;非法路径在 JSON 模式下返回类型化的 `invalid_cwd` JSON 错误。

`--allowedTools` 接受规范的 snake_case 工具名(例如 `read_file`、`glob_search`、`web_fetch`),也接受文档化的别名如 `read`、`glob`、`Read`、`WebFetch`。`claw status --output-format json` 暴露 `allowed_tools.available` 与 `allowed_tools.aliases`;非法值返回带 `tool_name`、`available`、`tool_aliases` 的类型化 `invalid_tool_name` JSON。子命令或其他旗标前缺少取值时返回 `missing_argument`,其中 `argument:"--allowedTools"`。

`--output-format` 接受大小写不敏感的 `text` 或 `json`,并规范化为小写规范模式。`CLAW_OUTPUT_FORMAT=json` 为脚本设定默认输出格式;显式 `--output-format` 旗标优先。重复该旗标会向 stderr 发警告,JSON 状态信封会暴露 `format_source`、`format_raw`、`format_overridden` 以便审计组合旗标;非法值返回带 `value` 与 `expected:["text","json"]` 的类型化 `invalid_output_format` JSON。

支持的权限模式(默认 `workspace-write`):

- `read-only`:只允许只读的本地工具,如文件读取、glob/grep 搜索、本地 skills、状态类报告。不允许修改 workspace、网络抓取/搜索工具或任意命令执行。
- `workspace-write`:安全默认值。允许读取,以及当前 workspace 内的直接文件编辑工具(write/edit/notebook/config/plan-mode 更新),同时仍把网络抓取/搜索、任意 shell 执行、子 agent 启动、REPL 子进程及其他全权限工具挡在显式提权之后。
- `danger-full-access`:允许所有已注册工具,包括任意命令执行、web 抓取/搜索、子 agent 启动、子进程 REPL 与无限制工具访问。仅在显式 `--permission-mode danger-full-access`、`--dangerously-skip-permissions`、`--skip-permissions`、环境变量或配置选择加入时才会启用。

CLI 当前支持的模型别名:

- `opus` → `claude-opus-4-7`
- `sonnet` → `claude-sonnet-4-6`
- `haiku` → `claude-haiku-4-5-20251213`

## 认证

### API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### OAuth

```bash
cd rust
export ANTHROPIC_AUTH_TOKEN="anthropic-oauth-or-proxy-bearer-token"
```

### 哪个环境变量放在哪里

`claw` 接受两个 Anthropic 凭据环境变量,二者**不可互换**——Anthropic 对不同凭据形态要求的 HTTP 头不同。把值放错槽位是我们见过的最常见 401 成因。

| 凭据形态 | 环境变量 | HTTP 头 | 常见来源 |
|---|---|---|---|
| `sk-ant-*` API key | `ANTHROPIC_API_KEY` | `x-api-key: sk-ant-...` | [console.anthropic.com](https://console.anthropic.com) |
| OAuth access token(不透明) | `ANTHROPIC_AUTH_TOKEN` | `Authorization: Bearer ...` | Anthropic 兼容代理或颁发 Bearer token 的 OAuth 流程 |
| OpenRouter key(`sk-or-v1-*`) | `OPENAI_API_KEY` + `OPENAI_BASE_URL=https://openrouter.ai/api/v1` | `Authorization: Bearer ...` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Ollama 本地实例 | `OLLAMA_HOST` | 无认证头(Ollama 不需要) | 本地 Ollama 服务 `http://127.0.0.1:11434` |

**为什么重要:** 如果把 `sk-ant-*` key 填进 `ANTHROPIC_AUTH_TOKEN`,Anthropic API 会返回 `401 Invalid bearer token`,因为 Bearer 头不接受 `sk-ant-*` key。修复只需换一个环境变量——把 key 移到 `ANTHROPIC_API_KEY`。较新的 `claw` 构建能识别这一精确形态(401 + Bearer 槽位里是 `sk-ant-*`)并在错误信息后附加指向修复方法的提示。

**如果你想用的是其他 provider:** 如果 `claw` 报告缺少 Anthropic 凭据,但你已导出 `OPENAI_API_KEY`、`XAI_API_KEY` 或 `DASHSCOPE_API_KEY`,多半是忘了给模型名加 provider 路由前缀。使用 `--model openai/gpt-4.1-mini`(OpenAI 兼容 / OpenRouter / Ollama)、`--model grok`(xAI)或 `--model qwen-plus`(DashScope),前缀路由器会无视环境里的其他凭据选择正确的后端。错误信息现在会点名检测到的环境变量。


### Windows PowerShell 的 provider 切换

同样的 provider 规则适用于 PowerShell。文档与测试中请使用占位值;真实 key 只放在私有环境里。验证切换时移除无关的 provider 环境变量,便于定位故障。

正常路由不需要 `CLAUDE_CODE_PROVIDER`;更推荐显式的模型前缀(如 `openai/`)加 provider 专属环境变量,让 PowerShell 示例保持可移植。

```powershell
# Anthropic 直连
$env:ANTHROPIC_API_KEY = "sk-ant-REPLACE_ME"
Remove-Item Env:\OPENAI_BASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue
.\target\debug\claw.exe --model "sonnet" prompt "reply with ready"

# OpenAI 兼容网关 / OpenRouter
Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
$env:OPENAI_BASE_URL = "https://openrouter.ai/api/v1"
$env:OPENAI_API_KEY = "sk-or-v1-REPLACE_ME"
.\target\debug\claw.exe --model "openai/gpt-4.1-mini" prompt "reply with ready"

# 本地 OpenAI 兼容服务
$env:OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
Remove-Item Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue
.\target\debug\claw.exe --model "llama3.2" prompt "reply with ready"
```

release 构件安装、持久化 `setx` 用法与 WSL 注意事项,见完整的 [Windows 安装与发布快速上手](./docs/windows-install-release.md)。

## 本地模型

`claw` 可通过 Anthropic 兼容或 OpenAI 兼容端点对接本地服务器与 provider 网关:Anthropic 兼容服务用 `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`,OpenAI 兼容服务用 `OPENAI_BASE_URL` + `OPENAI_API_KEY`。可复制的 Ollama、llama.cpp、vLLM、原生 `/v1/chat/completions` 及本地 skills 安装示例见 [`docs/local-openai-compatible-providers.md`](./docs/local-openai-compatible-providers.md)。

### Anthropic 兼容端点

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8080"
export ANTHROPIC_AUTH_TOKEN="local-dev-token"

cd rust
./target/debug/claw --model "claude-sonnet-4-6" prompt "reply with the word ready"
```

### OpenAI 兼容端点

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8000/v1"
export OPENAI_API_KEY="local-dev-token"

cd rust
./target/debug/claw --model "qwen2.5-coder" prompt "reply with the word ready"
```

### Ollama

```bash
export OLLAMA_HOST="http://127.0.0.1:11434"

cd rust
./target/debug/claw --model "llama3.2" prompt "summarize this repository in one sentence"
```

`OLLAMA_HOST` 是首选环境变量。Claw 自动把所有模型路由到本地 Ollama 端点,且无需 API key。旧的 `OPENAI_BASE_URL` + `OPENAI_API_KEY` 变通方案同样支持。

对带标点的 Ollama tag(例如 `qwen2.5-coder:7b`),两种方式都可行:

```bash
export OLLAMA_HOST="http://127.0.0.1:11434"

cd rust
./target/debug/claw --model "qwen2.5-coder:7b" prompt "reply with ready"
```

如果本地服务器暴露的模型 ID 含斜杠,加 `local/` 前缀,Claw 会选用 OpenAI 兼容传输并把其余部分原样上线:`--model "local/Qwen/Qwen3.6-27B-FP8"`。

### OpenRouter

```bash
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_API_KEY="sk-or-v1-..."

cd rust
./target/debug/claw --model "openai/gpt-4.1-mini" prompt "summarize this repository in one sentence"
```

### 阿里 DashScope(Qwen)

通过阿里官方 DashScope API 使用 Qwen 模型(比 OpenRouter 的限流更宽松):

```bash
export DASHSCOPE_API_KEY="sk-..."

cd rust
./target/debug/claw --model "qwen/qwen-max" prompt "hello"
# 或裸名:
./target/debug/claw --model "qwen-plus" prompt "hello"
```

以 `qwen/` 或 `qwen-` 开头的模型名自动路由到 DashScope 兼容模式端点(`https://dashscope.aliyuncs.com/compatible-mode/v1`)。**无需**设置 `OPENAI_BASE_URL`,也**无需**清掉 `ANTHROPIC_API_KEY`——模型前缀优先于环境凭据嗅探。

推理变体(`qwen-qwq-*`、`qwq-*`、`*-thinking`)在请求上线前自动剥离 `temperature`/`top_p`/`frequency_penalty`/`presence_penalty`(推理模型拒绝这些参数)。

## 支持的 Provider 与模型

`claw` 内置三个 provider 后端。provider 依据模型名自动选择,并回退到环境中存在的凭据。

### Provider 矩阵

| Provider | 协议 | 认证环境变量 | Base URL 环境变量 | 默认 Base URL |
|---|---|---|---|---|
| **Anthropic**(直连) | Anthropic Messages API | `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN` | `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` |
| **xAI** | OpenAI 兼容 | `XAI_API_KEY` | `XAI_BASE_URL` | `https://api.x.ai/v1` |
| **OpenAI 兼容** | OpenAI Chat Completions | `OPENAI_API_KEY` | `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| **DashScope**(阿里) | OpenAI 兼容 | `DASHSCOPE_API_KEY` | `DASHSCOPE_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |

OpenAI 兼容后端同时也是 **OpenRouter**、**Ollama** 及任何讲 OpenAI `/v1/chat/completions` 协议的服务的网关——把 `OPENAI_BASE_URL` 指向该服务即可。

**模型名前缀路由:** 模型名以 `openai/`、`local/`、`gpt-`、`qwen/`、`qwen-`、`kimi/` 或 `kimi-` 开头时,provider 由前缀决定,无视已设置的环境变量。这避免了多凭据环境下被误路由到 Anthropic。对默认 OpenAI API 和本地/私有 OpenAI 兼容端点,`openai/` 只是路由前缀,请求上线前会被剥离。对非本地自定义 `OPENAI_BASE_URL` 网关,含斜杠的 OpenAI 兼容 slug(例如 OpenRouter 风格的 `openai/gpt-4.1-mini`)会被保留,让网关收到它期望的模型 ID。`local/` 前缀是给含斜杠本地模型 ID 的显式逃生通道:前缀被剥离,其余部分原样发送。

### 已测试的模型与别名

以下是内置别名表中注册、且已知 token 上限的模型:

| 别名 | 解析后的模型名 | Provider | 最大输出 token | 上下文窗口 |
|---|---|---|---|---|
| `opus` | `claude-opus-4-7` | Anthropic | 32 000 | 200 000 |
| `sonnet` | `claude-sonnet-4-6` | Anthropic | 64 000 | 200 000 |
| `haiku` | `claude-haiku-4-5-20251213` | Anthropic | 64 000 | 200 000 |
| `grok` / `grok-3` | `grok-3` | xAI | 64 000 | 131 072 |
| `grok-mini` / `grok-3-mini` | `grok-3-mini` | xAI | 64 000 | 131 072 |
| `grok-2` | `grok-2` | xAI | — | — |
| `kimi` | `kimi-k2.5` | DashScope | 16 384 | 256 000 |
| `qwen-max` | `qwen-max` | DashScope | 8 192 | 131 072 |
| `qwen-plus` | `qwen-plus` | DashScope | 8 192 | 131 072 |
| `gpt-4.1` / `gpt-4.1-mini` / `gpt-4.1-nano` | 同名 | OpenAI 兼容 | 32 768 | 1 047 576 |
| `gpt-5.4` / `gpt-5.4-mini` / `gpt-5.4-nano` | 同名 | OpenAI 兼容 | 128 000 | 1 000 000 / 400 000 |

未匹配别名的模型名会在完成 provider 路由后原样透传。这就是使用 OpenRouter 模型 slug(配自定义 `OPENAI_BASE_URL` 的 `openai/gpt-4.1-mini`)、Ollama tag(`llama3.2` 或 `qwen2.5-coder:7b`)、含斜杠的本地 ID(`local/Qwen/Qwen3.6-27B-FP8`)或完整 Anthropic 模型 ID(`claude-sonnet-4-20250514`)的方式。

### 用户自定义别名

可在任意设置文件(`~/.claw/settings.json`、`.claw/settings.json` 或 `.claw/settings.local.json`)中添加自定义别名:

```json
{
  "aliases": {
    "fast": "claude-haiku-4-5-20251213",
    "smart": "claude-opus-4-7",
    "cheap": "grok-3-mini"
  }
}
```

项目级设置覆盖用户级设置。别名会经内置表解析,所以 `"fast": "haiku"` 也有效。

模型选择优先级:CLI 旗标 → 环境变量 → 配置 → 默认值。环境变量槽按序接受 `CLAW_MODEL`、`ANTHROPIC_MODEL`、`ANTHROPIC_DEFAULT_MODEL`;来自这些变量的别名会在 provider 启动前解析并校验。`claw --output-format json status` 暴露 `model_raw`、`model_alias_resolved_to`、`model_env_var`,自动化可以看到最终胜出的值。

### Provider 检测的工作方式

1. 解析后的模型名以 `claude` 开头 → Anthropic。
2. 以 `grok` 开头 → xAI。
3. 以 `openai/`、`local/` 或 `gpt-` 开头 → OpenAI 兼容。
4. 以 `qwen/`、`qwen-`、`kimi/` 或 `kimi-` 开头 → DashScope 兼容的 OpenAI 协议。
5. 设置了 `OPENAI_BASE_URL` 时,`llama3.2`、`qwen2.5-coder:7b` 这类本地风格未知模型名路由到 OpenAI 兼容客户端,用于本地/网关服务器。
6. 否则,`claw` 检查哪个凭据存在:先 Anthropic,再 OpenAI,再 xAI。若只设了 `OPENAI_BASE_URL`,依然路由到 OpenAI 兼容以支持免认证的本地服务器。
7. 都不匹配时,默认 Anthropic。


### Provider 诊断与自定义 OpenAI 兼容参数

API 层通过 `api::provider_diagnostics_for_model(model)` 暴露 provider 诊断快照:报告解析出的 provider、认证/base-url 环境变量、默认 base URL、是否使用 OpenAI 兼容协议、是否剥离推理调参、是否保留 DeepSeek V4 推理历史、代理支持、extra-body 支持,以及自定义 OpenAI 兼容网关是否保留含斜杠模型 ID。

对尚非一等请求字段的网关特性,`MessageRequest::extra_body` 可透传 provider 专属 JSON 参数,如 `web_search_options` 或 `parallel_tool_calls`。核心协议字段(`model`、`messages`、`stream`、`tools`、`tool_choice`、`max_tokens`、`max_completion_tokens`)受保护,无法通过 `extra_body` 覆盖。

## 文件上下文与导航

在 prompt 中使用 `@path/to/file` 提交仓库文件作为上下文,例如 `Read @src/app.ts and explain the bug`、`Compare @old.md and @new.md` 或 `Use @logs/error.txt as context and suggest a fix`。Prompt 历史、`Ctrl-r` 与长输出回滚来自你的 shell、终端或 tmux,而非 Claw 本身。回滚缓冲、附件与密钥脱敏指引见 [`docs/navigation-file-context.md`](./docs/navigation-file-context.md)。

## 常见问题(FAQ)

### Claw Code 只支持 Claude 吗?

不是。Claw Code 是 Claude Code 形状的工作流/runtime,不是 Claude 专属产品。依据配置,它可以指向 Anthropic、OpenAI 兼容/前缀路由/本地模型。非 Claude provider 可能对响应形态与 tool-call 兼容性要求更严格,部分工作流会比官方 Anthropic/OpenAI 路径更粗糙;provider 特有的身份泄露属于 bug,不是产品意图。本地 provider 示例见 [`docs/local-openai-compatible-providers.md`](./docs/local-openai-compatible-providers.md)。

### Codex 是怎么回事?

"codex" 一词出现在 Claw Code 生态中,但**不**指 OpenAI Codex(那个代码生成模型)。它在本项目中指:

- **`oh-my-codex` (OmX)**:位于 `claw` 之上的工作流与插件层,提供规划模式、并行多 agent 执行、通知路由等自动化能力。见 [PHILOSOPHY.md](./PHILOSOPHY.md) 与 [oh-my-codex 仓库](https://github.com/Yeachan-Heo/oh-my-codex)。
- **`.codex/` 目录**(如 `.codex/skills`、`.codex/agents`、`.codex/commands`):遗留查找路径,`claw` 仍会与主 `.claw/` 目录一起扫描。
- **`CODEX_HOME`**:可选环境变量,为用户级 skill 与命令查找指定自定义根目录。

`claw` **不**支持 OpenAI Codex 会话、Codex CLI 或 Codex 会话导入导出。若要使用 OpenAI 模型(如 GPT-4.1),按上文 [OpenAI 兼容端点](#openai-兼容端点) 与 [OpenRouter](#openrouter) 小节配置 OpenAI 兼容 provider。

## HTTP 代理支持

`claw` 在向 Anthropic、OpenAI 兼容与 xAI 兼容端点发起出站请求时,遵循标准的 `HTTP_PROXY`、`HTTPS_PROXY`、`NO_PROXY` 环境变量(大小写均可)。在启动 CLI 前设置,底层 `reqwest` 客户端会自动完成配置。

### 环境变量

```bash
export HTTPS_PROXY="http://proxy.corp.example:3128"
export HTTP_PROXY="http://proxy.corp.example:3128"
export NO_PROXY="localhost,127.0.0.1,.corp.example"
export CLAW_OUTPUT_FORMAT="json"   # 默认非交互输出格式;旗标可覆盖
export CLAW_LOG="debug"             # help/doctor 中会提示的 claw 专属日志级别
export RUST_LOG="claw=debug"        # help/doctor 中会提示的 Rust 日志约定

cd rust
./target/debug/claw prompt "hello via the corporate proxy"
```

### 编程式 `proxy_url` 配置项

作为按协议环境变量的替代,`ProxyConfig` 类型暴露 `proxy_url` 字段,作为同时覆盖 HTTP 与 HTTPS 流量的统一代理。设置 `proxy_url` 后,其优先级高于单独的 `http_proxy` 与 `https_proxy` 字段。

```rust
use api::{build_http_client_with, ProxyConfig};

// 从单一统一 URL(配置文件、CLI 旗标等)
let config = ProxyConfig::from_proxy_url("http://proxy.corp.example:3128");
let client = build_http_client_with(&config).expect("proxy client");

// 或直接设置字段并配合 NO_PROXY
let config = ProxyConfig {
    proxy_url: Some("http://proxy.corp.example:3128".to_string()),
    no_proxy: Some("localhost,127.0.0.1".to_string()),
    ..ProxyConfig::default()
};
let client = build_http_client_with(&config).expect("proxy client");
```

### 注意事项

- 同时设置 `HTTPS_PROXY` 与 `HTTP_PROXY` 时,安全代理作用于 `https://` URL,普通代理作用于 `http://` URL。
- `proxy_url` 是统一替代:设置后同时作用于 `http://` 与 `https://`,并覆盖按协议的字段。
- `NO_PROXY` 接受逗号分隔的主机后缀(例如 `.corp.example`)与 IP 字面量列表。
- 空值视为未设置,所以 `HTTPS_PROXY=""` 不会启用代理。
- 代理 URL 无法解析时,`claw` 回退为直连(无代理)客户端,保证既有工作流继续可用;若你预期请求走隧道,请复查 URL。

## Skills

在交互式 REPL 中使用 `/skills list`,或从直接 CLI 使用 `claw skills --output-format json` 检查已安装 skills。离线/本地安装时,安装包含 `SKILL.md` 的目录,然后在调用前确认发现的名称。`skills install`、`skills uninstall`、`agents create` 是本地文件系统生命周期命令,不需要 provider 凭据。

```text
/skills install /absolute/path/to/my-skill
/skills list
/skills uninstall my-skill
/skills my-skill
```

如果安装成功但调用时出现 provider HTTP 错误,请把 provider 配置当作独立问题处理:先运行 `claw doctor` 和一次单发 prompt 冒烟测试,再考虑重装 skill。完整检查清单见 [`docs/local-openai-compatible-providers.md`](./docs/local-openai-compatible-providers.md#local-skills-install-from-disk)。

## 常用操作命令

```bash
cd rust
./target/debug/claw status
./target/debug/claw sandbox
./target/debug/claw agents
./target/debug/claw agents create my-agent
./target/debug/claw mcp
./target/debug/claw skills
./target/debug/claw system-prompt --cwd .. --date 2026-04-04
```

## 安装外部 skill

`claw skills install <path>` 接受包含 `SKILL.md` 的本地 skill 目录或独立 markdown 文件。当配套仓库发布了希望经 `/skills` 使用的 skill prompt 时很有用。

例如,把 TweetClaw 安装为 X/Twitter 自动化 skill:

```bash
# 在包含 claw-code 的父目录中
git clone https://github.com/Xquik-dev/tweetclaw
cd claw-code/rust
./target/debug/claw skills install ../../tweetclaw/skills/tweetclaw
./target/debug/claw skills show tweetclaw
./target/debug/claw skills uninstall tweetclaw
```

TweetClaw 为 `claw` 用户提供 OpenClaw/Xquik 工作流的本地 skill 指南:推文搜索、回复搜索、关注者导出、监控、webhook 与带审批门禁的发文。请把 Xquik 凭据配置在 prompt 之外,避免把 API key 粘进聊天。

## 编写本地 agent

`claw agents create <name>` 为当前 workspace 生成 `.claw/agents/<name>.toml` 脚手架。脚手架刻意保持精简,便于在列出或调用 agent 前编辑描述、模型与推理力度:

```bash
./target/debug/claw agents create release-checker
./target/debug/claw agents list
```

## 会话管理

REPL 回合持久化在当前 workspace 的 `.claw/sessions/` 下。

```bash
cd rust
./target/debug/claw --resume latest
./target/debug/claw --resume latest /status /diff
```

常用的交互命令包括 `/help`、`/status`、`/cost`、`/config`、`/session`、`/model`、`/permissions`、`/export`。

## 配置文件解析顺序

运行时配置按此顺序加载,后者覆盖前者:

1. `~/.claw.json`
2. `~/.config/claw/settings.json`
3. `<repo>/.claw.json`
4. `<repo>/.claw/settings.json`
5. `<repo>/.claw/settings.local.json`

这一列表同时也是优先级链:项目本地设置覆盖项目设置,项目设置覆盖旧版项目 `.claw.json`,项目文件覆盖用户文件。`claw --output-format json config` 包含每个被发现文件的 `precedence_rank`、`wins_for_keys`、`shadowed_keys`,自动化无需重新实现合并顺序即可知道每个生效键由哪个文件控制。

## MCP 服务器校验

`claw mcp --output-format json` 即使兄弟条目格式错误,也会加载有效的 `mcpServers` 条目。JSON 列表信封区分配置总数与有效/无效子集(`configured_servers`、`total_configured`、`valid_count`、`invalid_count`、`servers[]`、`invalid_servers[]`,后者含 `name`、`error_field`、`reason`、`valid`)。

`status --output-format json` 在 `mcp_validation` 下呈现同样信息,`doctor --output-format json` 包含 `mcp validation` 检查,自动化因此可以在不丢失可用 MCP 服务器的前提下修复每个被拒条目。

## Hook 配置

`hooks.PreToolUse`、`hooks.PostToolUse`、`hooks.PostToolUseFailure` 接受旧版命令字符串,或带 `matcher` 与嵌套命令 hook 的对象式条目:

```json
{
  "hooks": {
    "PreToolUse": [
      "echo legacy hook",
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "scripts/audit-bash.sh" }
        ]
      }
    ]
  }
}
```

对象式 matcher 是可选的。存在时按工具名大小写不敏感匹配,支持 `*` 通配符以及逗号或竖线分隔的多个备选。嵌套 hook 的 `type` 可省略或设为 `"command"`;每个嵌套命令按配置顺序执行。
旧版裸字符串 hook 条目仍会加载以保持兼容,但会发弃用警告,建议迁移到对象式条目。未知的 hook 事件名(如 `Stop`、`Notification`)会被记为无效,而不影响有效 hook。`status --output-format json` 在 `hook_validation` 下镜像部分 hook 校验结果,含 `valid_count`、`invalid_count`、`invalid_hooks:[{event, index, hook_index, kind, error_field, reason, valid:false}]`。`doctor --output-format json` 包含 `hook validation` 检查,自动化可以在不丢失可用 hook 的前提下修复每个被拒条目。

## 项目指令规则

除根级指令文件(`CLAUDE.md`、`CLAW.md`、`AGENTS.md`、`.claw/CLAUDE.md`、`.claude/CLAUDE.md`、`.claw/instructions.md`)外,`claw` 还按排序加载以下 Markdown/文本规则文件:

- `<repo>/.claw/rules/`(`.md`、`.txt`、`.mdc`):共享项目规则。
- `<repo>/.claw/rules.local/`:个人本地规则;该路径已被 gitignore。

对每个被发现的目录,根级指令文件优先级为 `CLAUDE.md`、`CLAW.md`、`AGENTS.md`。发现范围在存在 git 根时限于当前 git 根,否则仅限当前目录,避免项目外的过期父级文件悄悄渗入 prompt。所有已加载文件都会进入 system prompt,并出现在 `status --output-format json` 的 `workspace.memory_files:[{path, source, origin, scope_path, outside_project, chars, contributes}]` 中;`claw doctor --output-format json` 包含 `memory` 检查,自动化无需解析 prompt 文本即可发现已加载与意外未加载的记忆文件候选。

默认情况下,`claw` 还会从常见 AI 编码工具导入检测到的规则,如 Cursor(`.cursorrules`、`.cursor/rules/`)、GitHub Copilot(`.github/copilot-instructions.md`)、Windsurf、Plandex 与 Crush。可在任意设置文件中用 `rulesImport` 控制:

```json
{
  "rulesImport": "none"
}
```

`"auto"`(默认)导入所有受支持框架;`"none"` 只加载 Claw 指令/规则文件;也可以用数组如 `["cursor", "copilot"]` 选择导入。

## Mock 一致性 harness

workspace 自带确定性的 Anthropic 兼容 mock 服务与一致性 harness。

```bash
cd rust
./scripts/run_mock_parity_harness.sh
```

手动启动 mock 服务:

```bash
cd rust
cargo run -p mock-anthropic-service -- --bind 127.0.0.1:0
```

## 验证

```bash
cd rust
cargo test --workspace
```

## Workspace 概览

当前的 Rust crate:

- `api`
- `commands`
- `compat-harness`
- `mock-anthropic-service`
- `plugins`
- `runtime`
- `rusty-claude-cli`
- `telemetry`
- `tools`

> 注:本文件超过 10000 字符,按预算翻译核心章节;原文中 MCP 校验与 hook 校验的两段超长 JSON 示例做了保留结构、精简字段的节译,完整字段请参见英文原版。
