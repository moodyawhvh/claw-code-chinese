> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。(原文为俄语版本;本文件超过 10000 字符,按预算翻译核心章节,Docker/Qdrant 部署等次要小节有删节,文末有说明。)

# claw-analog —— 如何运行及其工作原理

一个构建在与主 CLI [`claw`](rust/README.md) 相同 API 栈之上的最小 agent:Anthropic / OpenAI 兼容 / xAI 等 provider 依据模型名和环境变量自动选择(见 [USAGE.md](USAGE.md))。

以下示例中的**工作目录**是仓库克隆内的 **`claw-code-main\rust`** 文件夹。如果 PowerShell 提示符已经在 `…\claw-code-main\rust>`,**不要**再执行一次 `cd rust`(否则会变成 `rust\rust` 并报路径错误)。

## 环境要求

- 已安装 **Rust** 与 **cargo**(在 PATH 中:Windows 上通常为 `%USERPROFILE%\.cargo\bin`)。
- 所选 provider 的 API key(例如 `ANTHROPIC_API_KEY`)。

## 构建与帮助

```powershell
cd D:\path\to\claw-code-main\rust
cargo build -p claw-analog
cargo run -p claw-analog -- --help
```

### 诊断(`doctor`)

子命令 **`claw-analog doctor`**(它有自己独立的 `--help`):

- **配置预览** —— 展示 **`.claw-analog.toml`**(路径 `<workspace>/.claw-analog.toml` 或 **`--config`**)与主 run 相同旗标(**`--model`**、**`--permission`**、**`--preset`**、**`--output-format`**、**`--stream`**、**`--no-stream`**、**`--no-runtime-enforcer`**、**`--accept-danger-non-interactive`**,外加用于显示 profile 路径的 **`--profile`**)合并后的最终结果。会打印 NDJSON 契约(`schema`、`format_version`)、生效字段及 **provenance** 行(谁赢了:CLI、TOML 还是默认值);
- 常用环境变量状态(**不含**取值:只有 `set` / `unset` 与字符串长度);
- 从 cwd(或 **`--manifest-dir`**)向上查找 workspace,并默认执行 **`cargo check -p claw-analog`**(仅编译,**不**覆盖 `target\debug\claw-analog.exe` —— 否则在 Windows 上 `cargo run … doctor` 嵌套 `cargo build` 时常报"拒绝访问");
- **`--release-build`** —— 执行 **`cargo build --release -p claw-analog`**(二进制在 `target\release\`,与正在运行的 debug exe 不冲突);
- **`--no-build`** —— 跳过 cargo;
- **`--tcp-ping`**(别名 **`--mock`**)—— 对 **`ANTHROPIC_BASE_URL`** 中的主机:端口(或默认 `https://api.anthropic.com`)做 TCP **connect**;不校验 HTTP/TLS 与响应体。

示例(在 `…\claw-code-main\rust` 目录下):

```powershell
cargo run -p claw-analog -- doctor
cargo run -p claw-analog -- doctor --no-build
cargo run -p claw-analog -- doctor --tcp-ping
cargo run -p claw-analog -- doctor -w D:\path\to\repo --preset implement
cargo run -p claw-analog -- doctor --release-build
```

### 不调用 API 的配置校验(`config validate`)

子命令 **`claw-analog config validate`**:

- 解析 **`.claw-analog.toml`**(默认 `<workspace>/.claw-analog.toml`,可用 **`--config`** 覆盖),输出简要 **merge preview**(类似 `doctor`,但**只有 TOML + 默认值**,不含主 run 旗标);
- 校验 **`profile.toml`**:顺序与 run 相同(`--profile`、TOML 中的 `profile` 字段,否则默认 `~/.claw-analog/profile.toml` 若存在);
- **不**发起任何 LLM / API 网络请求。

**`--strict`** —— 当配置文件不存在或 profile 不可读时报错(退出码 1)。

```powershell
cargo run -p claw-analog -- config validate -w D:\path\to\repo
cargo run -p claw-analog -- config validate --strict -w .
```

### Shell 补全(`complete`)

向 **stdout** 输出自动补全脚本(按你的 shell 文档重定向到相应文件):

```powershell
cargo run -p claw-analog -- complete powershell >> $PROFILE
# bash:zsh:fish —— 见 `complete --help` 输出
```

可用值:**`bash`**、**`zsh`**、**`fish`**、**`powershell`**(别名 **`pwsh`**)。

## 主要命令

单条任务作为参数传入(或经 **stdin** 传入文本):

```powershell
# 在 ...\claw-code-main\rust 下
cargo run -p claw-analog -- -w D:\path\to\repo "简要描述 rust/crates 的结构"
```

**实时输出**(经 `stream_message` 的 SSE):

```powershell
cargo run -p claw-analog -- --stream -w . "用两句话解释 claw-analog"
```

允许向 workspace **写文件**:

```powershell
cargo run -p claw-analog -- --permission workspace-write -w . "在 crates/claw-analog/Cargo.toml 开头加一条注释"
```

关闭 **`runtime::PermissionEnforcer`** 校验(仅剩自身的路径限制;不推荐):

```powershell
cargo run -p claw-analog -- --no-runtime-enforcer -w . "…"
```

常用限制旗标(CLI **覆盖** `.claw-analog.toml` 中的取值,见下):

| 旗标 | 默认值 | 用途 |
|------|------------------------|------------|
| `--max-read-bytes` | 262144 | `read_file` / `grep_workspace` / `git_diff` / `git_log` 的最大字节数 |
| `--max-turns` | 24 | "模型 → 工具 → 模型" 的最大轮数 |
| `--max-list-entries` | 500 | `list_dir` 的行数上限 |
| `--grep-max-lines` | 200 | `grep_workspace` **合计**匹配行数上限(可跨多文件;单文件可用 `max_lines` 设得更小) |
| `--glob-max-paths` | 2000 | `glob_workspace` 及 `grep_workspace` 内展开 glob 时返回的最大路径数 |
| `--glob-max-depth` | 32 | glob 的目录遍历深度(经 `walkdir`),无无限递归 |
| `--output-format` | `rich` | `json` —— stdout 输出 NDJSON,供脚本与 agent 使用 |
| `--print-tools` | — | 列出在最终 `permission` / enforcer 下生效的工具,然后退出(**不**发起 prompt 与 API 调用) |
| `--lang` | `en` | system 中的提示:`en` 或 `ru`(回答语言;**不**改变 API 中的模型 id) |
| `--preset` | — | `none` \| `audit` \| `explain` \| `implement` —— 见下文 |
| `--session` | — | JSON 会话文件路径(非绝对路径时相对于 `-w`):保存历史并支持 resume |
| `--save-session` | — | 额外路径:每次保存时把同一会话快照再写一份(可**不**带 `--session`,仅用于跑完后导出 JSON) |
| `--profile` | — | 含 `line` 字段的 TOML(并入 system)。不传旗标时依次尝试 `%USERPROFILE%\.claw-analog\profile.toml`(Windows)/ `~/.claw-analog/profile.toml` |
| `--permission` | `read-only` | 见下:`read-only`、`workspace-write`、`prompt`、`danger-full-access`、`allow` |
| `--accept-danger-non-interactive` | — | 当 stdin **不是** TTY(CI;自担风险)时允许 `danger-full-access` / `allow`。TOML 写法:`accept_danger_non_interactive = true` |

默认配置从 **`<workspace>/.claw-analog.toml`** 读取(若存在);其他路径用 **`--config PATH`**。TOML 中的未知键会导致解析错误(严格 schema)。

`.claw-analog.toml` 示例:

```toml
model = "sonnet"
stream = true
output_format = "rich"
permission = "read-only"
language = "en"
preset = "audit"
session = ".claw-analog.session.json"
profile = "~/.claw-analog/profile.toml"
no_runtime_enforcer = false
accept_danger_non_interactive = false
max_read_bytes = 262144
max_turns = 24
max_list_entries = 500
grep_max_lines = 200
glob_max_paths = 2000
glob_max_depth = 32
# 可选:RAG(`claw-rag-service`)—— 见下文 RAG 小节
# rag_base_url = "http://127.0.0.1:8787"
# rag_timeout_secs = 30
# rag_top_k_max = 32
```

**RAG(`retrieve_context`):** 当设置了 **`RAG_BASE_URL`**(环境变量)或 `.claw-analog.toml` 中的 **`rag_base_url`** 非空时,工具集中会加入 **`retrieve_context`**(对已索引 workspace 做语义检索)。取值是 HTTP 服务根地址,不带 `/v1` 后缀(请求发往 `{base}/v1/query`)。超时与 **`top_k`** 上限由 **`rag_timeout_secs`** 与 **`rag_top_k_max`** 控制(默认 30 秒与 32;硬上限 256)。索引仍由独立的 **`claw-rag-service`** 命令完成,见 [`docs/rag-web-ui.md`](docs/rag-web-ui.md)。

**`permission`**(与完整 `claw` 相同,TOML 中用同样的字符串):

| 取值 | `write_file` 工具 | 非交互(stdin 非 TTY) |
|----------|-------------------------|------------------------------|
| `read-only` | 不可用 | 允许 |
| `workspace-write` | 可用(限于 `-w` 内) | 允许 |
| `prompt` | 不可用(此 harness 中 Enforcer 不允许无确认写入) | stderr 给出警告;需要自动写入请用 `workspace-write` |
| `danger-full-access`、`allow` | 可用 | **禁止**,除非设置 `--accept-danger-non-interactive` 或 TOML 中 `accept_danger_non_interactive = true` |

命令行 **`--stream`** 开启流式;**`--no-stream`** 显式关闭(在文件里 `stream = true` 时有用)。

TOML 中的 **`language`**:`en` 或 `ru`(与 **`--lang`** 相同取值);CLI 优先。

### 会话(`--session`)

JSON 文件(版本 `1`):元数据 `workspace`、`model`、可选 `preset`,以及 API 格式(`role` + `content`)的 `messages` 数组。带已有文件启动时,**追加加载**历史,当前请求文本(参数或 stdin)作为**新的**用户消息加入。每个完整的工具轮之后以及无 `tool_use` 结束时都会保存状态。

**`--save-session`** —— 与 `--session` 相同的文件格式:在每个本来会更新会话文件的步骤,额外写一份副本(若路径与 `--session` 相同则不重复写)。不带 **`--session`** 时,可把单次运行的历史收集成 JSON,供脚本或后续 **`--session`** 使用,免得手工拼 `messages`。

**风险:** 文件中可能出现**密钥**(`read_file` 的输出、日志中的 key),文件不做加密;长历史会**消耗更多** API token。使用 **`--session`** 或 **`--save-session`** 时 stderr 会打印提醒。`workspace` / `model` / `preset` 与当前运行不一致会给出**警告**,但运行继续。

### 预设(`--preset`)

向 system prompt 追加一小段文字(审计 / 讲解 / 改代码)。工具集仍由 **permission** 决定:对 **`implement`**,若 CLI 和文件都没指定 `permission`,会默认代入 **workspace-write**(以便有 `write_file`)。文件中显式的 `permission = "read-only"` 或 CLI 的 `--permission read-only` 优先。

### Profile(`profile.toml`)

迷你文件:

```toml
line = "一句简短的风格提示(作为 system 中的一行)。"
```

限制:文件不超过 **2048** 字节;trim 后单行不超过 **512** 个 Unicode 字符(否则截断并告警)。内容以单行形式并入 system:`Learner hint: …`。

## 工具集(无任意 shell)

| 名称 | 模式 | 说明 |
|-----|--------|----------|
| `read_file` | read-only+ | 读取 `-w` 下的 UTF-8 文件 |
| `list_dir` | read-only+ | 目录列表(非递归) |
| `glob_workspace` | read-only+ | 列出 `-w` 下的**文件路径**:参数 `pattern`(相对 `root` 的 glob,斜杠 `/`)、可选 `root`(默认 `.`)、`max_paths`(会被 CLI 上限截断)。模式中不允许 `..`。 |
| `grep_workspace` | read-only+ | 按行做**字面量**子串搜索;选择器三选一:`path`、`paths` 数组或 `glob`(+ 可选 `glob_root`)。总行数预算由 `max_lines` 与 `--grep-max-lines` 约束。多文件时行格式:`相对/路径:行号:内容`。 |
| `grep_search` | read-only+ | 与 `grep_workspace` 相同的处理器(兼容完整 `claw` 的 prompt)。 |
| `git_diff` | read-only+ | 在 `-w` 仓库内执行 `git diff`(无颜色)。可选 `cached`(已暂存)、`rev_range`、`context_lines`、`paths`。输出受 `--max-read-bytes` 限制。 |
| `git_log` | read-only+ | 在 `-w` 仓库内执行 `git log`(无颜色)。可选 `max_count`(默认 20)、`rev_range`、`paths`。输出受 `--max-read-bytes` 限制。 |
| `retrieve_context` | read-only+ | 仅当设置 **`RAG_BASE_URL`** 或 TOML **`rag_base_url`** 时可用:向 `claw-rag-service` 发 **`POST {base}/v1/query`**,返回 chunk 路径与片段(限制见上)。 |
| `write_file` | `workspace-write`、`danger-full-access` 或 `allow` | 写文件;必要时自动创建父目录(`prompt` 模式下 Enforcer 不允许写入) |

## 工作原理

1. **workspace 根**(`-w`)会被规范化为 canonical 路径;工具中所有路径均为**相对路径**,不允许 `..` 和绝对路径段。
2. 访问文件前校验真实路径仍**在**根内(symlink / `canonicalize`)。
3. **权限策略**(未用 `--no-runtime-enforcer` 关闭时):与主 CLI 相同的实体——对工具用 `PermissionPolicy` + `PermissionEnforcer::check`,写文件用 `check_file_write`。
4. **Agent 循环**:请求 provider → 若 `stop_reason == tool_use` 则执行调用,结果以 `tool_result` 进入历史 → 下一轮。
5. **流式**:`--stream` 时助手文本随增量到达即打印;下一轮的历史从 SSE 收集,与完整管道一致(块索引 + JSON tool input)。由文件配置开启时,可用 **`--no-stream`** 关闭。

`[claw-analog] ...` 形式的日志写入 **stderr**。**rich** 模式下模型回复以普通文本进入 **stdout**;**json** 模式下 **stdout** 只有 **NDJSON**(见下)。

## JSON 输出(CI 与外部 agent)

旗标 **`--output-format json`** 把 stdout 切换为**逐行 JSON 流**(一行一个对象)。字段含义稳定,但集合可能扩展。

主要 `type`:

| `type` | 时机 |
|--------|--------|
| `run_start` | 运行开始:**`schema`**(`claw-analog-ndjson`)、**`format_version`**,以及 `workspace`、`model`、`stream`、`permission`、可选 `preset`、`session`、可选 `session_save`、布尔 **`rag_enabled`**(是否具备 `retrieve_context` 的服务地址) |
| `turn_start` | 与模型的一轮开始(`turn`) |
| `assistant_text_delta` | 仅 `--stream`:助手文本片段 |
| `assistant_turn` | 一轮结果:`stop_reason`、`usage`、完整 `text`、`tool_calls` 数组 |
| `tool_result` | 工具执行后:`name`、`tool_use_id`、`is_error`、`output`(可能截断)、`truncated`、`output_len_chars` |
| `run_end` | 成功结束(`ok: true`) |
| `error` | 出错(失败或空 prompt 时单独一行输出) |

示例(PowerShell):逐行解析该流用 **`jq`** 或任意 JSON 解析器都很方便。

```powershell
# 在 ...\claw-code-main\rust 下
$env:ANTHROPIC_API_KEY = "sk-ant-..."
cargo run -p claw-analog -- --output-format json -w . "Summarize rust/README.md" 2>$null | ForEach-Object { $_ | ConvertFrom-Json | Select-Object -ExpandProperty type }
```

带 **`--stream`** 时,stdout 先出现 `assistant_text_delta` 事件,随后同一轮会有一行 `assistant_turn`,其中携带拼装完成的完整 `text`(便于可复现日志)。

### 对 agent 的限制与风险

- **`tool_result.output`** 中大文件会被截断(约 32 KiB UTF-8),字段 **`truncated`: true**。
- **密钥**:未经滤不要把 stderr 原样送进公开日志;`output` 理论上可能包含被读文件的内容。
- 编排器契约:NDJSON 取自 stdout,诊断取自 stderr;出错时返回码 ≠ 0。第一行 **`run_start`** 应校验 **`schema`** 与 **`format_version`**;**`run_start`** 还会暴露 workspace 路径与模型——分享日志时请注意。

## 无真实网络的自动化测试

单元测试与针对本地 **mock-anthropic-service** 的集成测试:

```powershell
# 在 ...\claw-code-main\rust 下
cargo test -p claw-analog
```

**GitHub Actions** 中有独立 job **`claw-analog (test + clippy -p)`**,运行 `cargo test -p claw-analog` 与 `cargo clippy -p claw-analog --no-deps`(此外还有全 workspace 的 `cargo test` / `clippy`)。

并行跑测试时,Anthropic 相关环境变量仅对 mock 场景用 **mutex** 隔离;若不稳定,可运行 `cargo test -p claw-analog -- --test-threads=1`。

## RAG 服务(`claw-rag-service`)简述

workspace 索引与 HTTP API 在 **`cargo run -p claw-rag-service`**(`ingest` + `serve`)中。`serve` 之后打开 **`http://127.0.0.1:8787/`** 即可使用轻量 UI(stats + 搜索)。`claw-analog` 通过 **`RAG_BASE_URL`** / `retrieve_context` 接入。要点:

- `ingest` 可重复传入 **`--workspace`**,支持**跨仓库 RAG**(多个仓库入同一个库/集合),响应中的 `path` 形如 `repoId:relative/path` 以避免路径冲突;
- 本地测试可设 `CLAW_RAG_MOCK_PROVIDERS=1` 启用 mock 嵌入,无需 key 与网络;
- 大仓库建议用 Docker 起本地 **Qdrant**(gRPC 6334),通过 `CLAW_RAG_QDRANT_URL` / `CLAW_RAG_QDRANT_COLLECTION` 接入,`ingest` 加 `--features qdrant-index`,集合不存在时会按嵌入维度自动创建;仓库也提供 `docker compose up --build` 一键起 Qdrant + claw-rag-service 的方案;
- 完整的环境变量、Docker/Qdrant 部署细节与网页 UI 说明见 [`docs/rag-web-ui.md`](docs/rag-web-ui.md)(本节为节选,未逐条翻译)。

## Auto-TDD(`write_file`/`edit_file` 后自动校验)

在完整 `claw`(及其他 `runtime` 消费方)中,可通过 `.claw/settings.json` 在写工具成功后自动运行 lint/测试:

```json
{
  "autoTdd": {
    "enabled": true,
    "tools": ["write_file", "edit_file"],
    "commands": [
      "cd rust && cargo fmt",
      "cd rust && cargo clippy --workspace --all-targets -- -D warnings",
      "cd rust && cargo test --workspace"
    ]
  }
}
```

## 与完整 `claw` 的差异

- 工具集更窄(没有 bash / MCP / 插件)。
- 更容易审计,可通过 `--permission` 与各项限制约束。
- 主产品仍是 `cargo run -p rusty-claude-cli` → 二进制 `claw`。

## 后续开发

计划与想法清单(包括借鉴自 DeepTutor 等产品层的部分)见仓库根目录的 [`futute.md`](futute.md)。

> 注:原文为俄语;本文件超过 10000 字符,已按预算翻译核心章节。原版中 "Qdrant(推荐本地方案)via Docker" 与 "docker compose 部署" 两节的具体命令块未逐条翻译,仅作要点归纳,完整步骤请参见原文件与 docs/rag-web-ui.md。
