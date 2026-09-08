> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。

# 项目知识库

**生成时间:** 2026-08-16
**提交:** b71afdd
**分支:** main

## 概览
Claw Code:`claw` CLI agent 框架(Claude Code 风格)的公开 Rust 实现。权威代码位于 `rust/`;本仓库是一个由 agent 管理的展示项目(按 README 所述由 harness 执行 plan/execute/verify),不是手工维护的产品。`src/` 是配套的 Python 移植/一致性(parities)工作区,并非生产代码。

## 目录结构
```
claw-code/
├── rust/      # 权威 Cargo 工作区:11 个 crate,`claw` 二进制
├── src/       # Python 移植工作区 + reference_data/ 一致性快照
├── tests/     # 对 src/ 与 scripts/ 的 Python unittest 验证(stdlib unittest)
├── docs/      # g0XX 门禁验证地图 + 主题文档
├── scripts/   # fmt.sh、dogfood-build.sh、roadmap/board 辅助脚本
├── assets/    # 仅存放 README 图片
└── install.sh, Containerfile, docker-compose.yml
```

## 去哪找
| 任务 | 位置 | 说明 |
|------|------|------|
| CLI 子命令 | rust/crates/rusty-claude-cli/src/main.rs | 手写解析器;CliAction 枚举约在 L1162;run() 内分发在 L995-1158 |
| 会话/权限/MCP | rust/crates/runtime/src/ | 47 个扁平模块 |
| Provider 客户端 | rust/crates/api/src/providers/ | anthropic.rs + openai_compat.rs |
| 工具定义 | rust/crates/tools/src/lib.rs | 55 个工具的 spec 表 L484-1348 |
| 斜杠命令 | rust/crates/commands/src/lib.rs | 120+ 条 spec 表 L60-1047 |
| 插件/hook | rust/crates/plugins/src/ | manifest 为 .claude-plugin/plugin.json |
| 精简 agent harness | rust/crates/claw-analog/src/lib.rs | lib+bin;基于 api+runtime 的工具循环 |
| RAG HTTP 服务 | rust/crates/claw-rag-service/src/ | axum;SQLite + 可选 Qdrant |
| 测试 mock 服务器 | rust/crates/mock-anthropic-service/ | 以 SCENARIO_PREFIX 脚本化响应 |
| Python 移植 CLI | src/main.py | argparse:manifest、parity-audit、graphs |
| 一致性参考数据库 | src/reference_data/subsystems/ | TS 归档的 29 份 JSON 快照 |

## 代码地图
| 符号 | 类型 | 位置 | 引用数 | 作用 |
|------|------|------|--------|------|
| Session | struct | runtime/src/session.rs:117 | 229 | 会话持久化/生命周期 |
| ConfigLoader | struct | runtime/src/config.rs:409 | 83 | 配置 schema/加载 |
| PluginManager | struct | plugins/src/lib.rs | 48 | 插件安装/注册 |
| PermissionEnforcer | struct | runtime/src/permission_enforcer.rs:27 | 35 | 分发前的权限门禁 |
| ConversationRuntime | struct | runtime/src/conversation.rs:130 | 32 | 会话循环驱动器 |
| McpServerManager | struct | runtime/src/mcp_stdio.rs:488 | 30 | MCP JSON-RPC 进程 |
| HookRunner | struct | runtime/src/hooks.rs:155 | 25 | shell hook 执行 |
| CliAction | enum | rusty-claude-cli/src/main.rs:1162 | — | 25 个子命令变体 |
| mvp_tool_specs | fn | tools/src/lib.rs:484 | — | 静态 55 工具表 |
| SLASH_COMMAND_SPECS | const | commands/src/lib.rs:60 | — | 120+ 斜杠命令 |

(引用数 = 在 rust/crates 内的 rg 统计;映射期间 rust-analyzer 引用查询超时。)

## 约定
- 工作区全局 `unsafe_code = "forbid"`;每个 crate 通过 `[lints] workspace = true` 选择加入;clippy all=warn、pedantic=allow
- Edition 2021、resolver 2、publish=false;不固定 rust-toolchain(CI 跟随 stable);没有 rustfmt.toml/clippy.toml —— 使用默认配置
- 特意的超大扁平文件(main.rs 19.8k 行、tools/lib.rs 10.9k 行、commands/lib.rs 7.2k 行):组织方式是按位置排布 —— 类型 → spec 表 → 分发 → 处理器 → 文件末尾测试
- 处处存在双输出路径:`render_x` + `render_x_json`;JSON 错误走 **stdout**,文本错误走 **stderr**
- 测试:以内联 `#[cfg(test)] mod tests` 为主;集成测试通过 `CARGO_BIN_EXE_claw` 对 mock-anthropic-service 起子进程;到处使用 tempfile;会改动环境变量的测试通过 env_lock/test_env_lock 串行化
- 注释携带 issue 编号(#824、#146);门禁测试按路线图门禁命名(g004_conformance.rs)
- Python 侧:仅用标准库,`python -m unittest`;src/ 中 camelCase(QueryEngine.py)与 snake_case 文件名混用

## 本项目的反模式
- 永远不要 `cargo install claw-code` —— crates.io 上的占位包已弃用,会安装 `claw-code-deprecated.exe`;请从源码构建
- 禁用的文档字符串(由 .github/scripts/check_doc_source_of_truth.py 在 CI 强制):旧组织链接 `github.com/Yeachan-Heo/claw-code`、`github.com/code-yeongyu/claw-code`、`discord.gg/6ztZB9jvWq`、`assets/clawd-hero.jpeg`
- 已弃用的配置键:`permissionMode` → `permissions.defaultMode`;`enabledPlugins` → `plugins.enabled`;环境变量 `RUSTY_CLAUDE_PERMISSION_MODE` 已失效
- 策略上禁止直接推送到 main(`main_push_forbidden` 审批范围)
- 自动化通道不得合并/关闭远程 PR/issue(docs/anti-slop-triage.md)
- `claw init` 不得生成 `dontAsk` 权限模式(在 output_format_contract.rs 中以回归测试钉死)
- 文件级 `#![allow(dead_code)]`(main.rs、session_control.rs)属于被容忍的遗留 —— 不要扩散这种模式

## 独有风格
- 自举(dogfood)构建:scripts/dogfood-build.sh 注入 GIT_SHA;`claw version` 的来源信息必须等于 HEAD
- Mock 一致性:rust/mock_parity_scenarios.json 驱动 CLI 子进程与 MockAnthropicService 对比
- 自举测试使用 `CLAW_CONFIG_HOME=$(mktemp -d)` 实现配置隔离
- 环境变量契约:GIT_SHA(构建)、CLAW_CONFIG_HOME(配置目录)、OLLAMA_HOST(provider 覆盖)、各 provider 的 `*_API_KEY`/`*_BASE_URL`

## 常用命令
```bash
scripts/fmt.sh --check                 # fmt 检查(应用格式化:scripts/fmt.sh)
cd rust && cargo clippy --workspace --all-targets -- -D warnings
cd rust && cargo test --workspace
cd rust && cargo build -p rusty-claude-cli   # 二进制:rust/target/debug/claw
python -m unittest discover -s tests   # Python 测试套件
python .github/scripts/check_doc_source_of_truth.py && scripts/roadmap-check-ids.sh   # docs/roadmap CI
```

## 备注
- `claw` 二进制来自 crate `rusty-claude-cli`(包名与二进制名不一致)
- rust-ci.yml 仅在 rust/**、docs/** 及列出的元文件变化时触发(路径过滤)
- CI 的 clippy 任务没有加 `-D warnings` —— 弱于文档所述门禁;已知的历史失败记录在 docs/g002/g003 地图中
- `claw acp` 是状态占位 stub,不是真正的 ACP 服务器
- rust/ 中提交了 harness 点目录(.clawd-agents/、.omc/、.sandbox-home/)—— 这是有意为之
