> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。

# CLAUDE.md

本文件为 Claude Code(claude.ai/code)在本仓库中处理代码时提供指引。

## 检测到的技术栈
- 语言:Rust。
- 框架:未从支持的起始标记中检测到框架。

## 验证
- 在仓库根目录运行 Rust 验证:`scripts/fmt.sh --check`;格式化用 `scripts/fmt.sh`。在 `rust/` 下运行 clippy/测试:`cargo clippy --workspace --all-targets -- -D warnings`、`cargo test --workspace`
- `src/` 与 `tests/` 同时存在;行为变化时请同步更新两侧。

## 仓库形态
- `rust/` 存放 Rust workspace 与活跃的 CLI/runtime 实现。
- `src/` 存放源文件,应与生成的指引和测试保持一致。
- `tests/` 存放验证面,代码改动时应一并审查。

## 协作约定
- 优先小而可审查的改动,保持生成的引导文件与仓库实际工作流一致。
- 共享默认值放在 `.claude.json`;`.claude/settings.local.json` 仅用于机器本地覆盖。
- 不要自动覆盖已有的 `CLAUDE.md` 内容;当仓库工作流变化时,有意识地更新它。
