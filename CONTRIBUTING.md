> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。

# 参与 Claw Code 贡献

感谢你帮助改进 Claw Code。本仓库是一个以 Rust 为主的 CLI 工作区,附带配套文档与兼容性测试样本。

## 基本准则

- 保持改动小而可审查,并与具体的 issue 或行为挂钩。
- 不要提交密钥、API key、包含凭据的会话记录,或构建生成的产物。
- 在新增依赖之前,优先复用现有的 crate 边界和工具函数。
- 当用户可见的命令、配置项或 provider 行为发生变化时,同步更新文档。
- 保证示例可以安全地复制粘贴。使用 `sk-ant-...` 这类占位符 key,除非文中明确说明,否则避免给出需要真实凭据的命令。

## 本地环境搭建

```bash
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace
cargo test --workspace
```

在 Windows PowerShell 上,同样在 `rust` 工作区内构建,并带 `.exe` 后缀运行二进制:

```powershell
cd claw-code\rust
cargo build --workspace
.\target\debug\claw.exe --help
```

## 本地推送前构建门禁

安装仓库内置的 Git hook,以便在推送前拦截过时的编译错误:

```bash
git config core.hooksPath .github/hooks
```

这条命令会把仓库的 Git hook 目录设置为 `.github/hooks`;如果你已经在使用自定义的 `core.hooksPath`,请改为复制或串联 `.github/hooks/pre-push`。该 hook 会先运行 ROADMAP id 守卫,然后在仓库根目录执行
`cargo build --manifest-path rust/Cargo.toml --workspace --locked`。如果你是纯文档推送、必须跳过 cargo 构建,可以设置 `SKIP_CLAW_PRE_PUSH_BUILD=1`;此时 hook 仍会运行 ROADMAP 守卫,并在使用 cargo 构建逃生通道时打印提示。

## ROADMAP id 分配

在向 ROADMAP 追加新的数字条目之前,先 pull/rebase 到最新的 `main`,从你即将编辑的文件中分配 id,并在推送前运行重复 id 守卫:

```bash
git pull --rebase
NEXT=$(scripts/roadmap-next-id.sh)
# 把 "${NEXT}. **...**" 追加到 ROADMAP.md
scripts/roadmap-check-ids.sh
```

重复 id 守卫默认只检查 helper 时代的 id(`>=723`),因此既能捕获新增的"乐观追加"冲突,又不会对历史路线图中已存在的旧编号列表误报。等那些历史冲突清理完毕后,可以用 `scripts/roadmap-check-ids.sh --min-id 1` 做全文件严格审计。

## 提交 Pull Request 前的检查

先运行与你的改动相关的最小测试集合;当你触及共享 runtime、CLI 或文档面时,再运行更广的检查:

```bash
cd rust
cargo fmt --all --check
cargo test --workspace
cargo clippy --workspace
```

对于文档与发布就绪度相关的改动,还要运行:

```bash
python .github/scripts/check_doc_source_of_truth.py
python .github/scripts/check_release_readiness.py
```

## Pull Request 指南

- 说明这次改动对用户可见的原因。
- 列出你运行过的命令以及已知未覆盖的部分。
- 明确指出对 CLI 输出、JSON schema、插件契约、provider 行为或 Windows/PowerShell 示例的兼容性风险。
- 不要在功能或修复 PR 中夹带无关的清理工作。

## 许可证

提交贡献即表示你同意你的贡献按本项目的 [MIT 许可证](./LICENSE) 授权。
