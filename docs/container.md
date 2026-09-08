> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。

# 容器优先的 claw-code 工作流

在本文件加入之前,仓库的 Rust runtime 已经具备**容器检测**能力:

- `rust/crates/runtime/src/sandbox.rs` 检测 Docker/Podman/容器标记,如 `/.dockerenv`、`/run/.containerenv`、匹配的环境变量以及 `/proc/1/cgroup` 线索。
- `rust/crates/rusty-claude-cli/src/main.rs` 通过 `claw sandbox` / `cargo run -p rusty-claude-cli -- sandbox` 报告暴露该状态。
- `.github/workflows/rust-ci.yml` 运行在 `ubuntu-latest` 上,但**没有**定义 Docker 或 Podman 容器任务。
- 在本次变更之前,仓库**没有**签入 `Dockerfile`、`Containerfile` 或 `.devcontainer/` 配置。

本文档加入了一个小型签入 `Containerfile`,让 Docker 与 Podman 用户拥有一条规范的容器工作流。

## 签入的容器镜像做什么用

根目录的 [`../Containerfile`](../Containerfile) 提供一个可复用的 Rust 构建/测试 shell,并附带本 workspace 常用的额外软件包(`git`、`pkg-config`、`libssl-dev`、证书)。

它**不会**把仓库复制进镜像。相反,推荐流程是把你的检出目录 bind-mount 到 `/workspace`,这样编辑内容仍保留在宿主机上。

## 构建镜像

在仓库根目录执行:

### Docker

```bash
docker build -t claw-code-dev -f Containerfile .
```

### Podman

```bash
podman build -t claw-code-dev -f Containerfile .
```

## 在容器中运行 `cargo test --workspace`

以下命令挂载仓库、把 Cargo 构建产物挡在工作树之外,并从 `rust/` 的 Rust workspace 运行。

### Docker

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev \
  cargo test --workspace
```

### Podman

```bash
podman run --rm -it \
  -v "$PWD":/workspace:Z \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev \
  cargo test --workspace
```

如果想要完全干净的重建,在 `cargo test --workspace` 前加 `cargo clean &&`。

## 在容器中打开 shell

### Docker

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev
```

### Podman

```bash
podman run --rm -it \
  -v "$PWD":/workspace:Z \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev
```

在 shell 内:

```bash
cargo build --workspace
cargo test --workspace
cargo run -p rusty-claude-cli -- --help
cargo run -p rusty-claude-cli -- sandbox
```

`sandbox` 命令是个很好的健全性检查:在 Docker 或 Podman 内,它应报告 `In container true` 并列出 runtime 检测到的标记。

## 同时挂载本仓库与另一个仓库

如果你想让 `claw` 处理第二个检出目录,同时保持 `claw-code` 自身以读写方式挂载:

### Docker

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -v "$HOME/src/other-repo":/repo \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev
```

### Podman

```bash
podman run --rm -it \
  -v "$PWD":/workspace:Z \
  -v "$HOME/src/other-repo":/repo:Z \
  -e CARGO_TARGET_DIR=/tmp/claw-target \
  -w /workspace/rust \
  claw-code-dev
```

然后,例如:

```bash
cargo run -p rusty-claude-cli -- prompt "summarize /repo"
```

## 注意事项

- Docker 与 Podman 使用同一个签入的 `Containerfile`。
- Podman 示例中的 `:Z` 后缀用于 SELinux 重新打标;在 Fedora/RHEL 系主机上请保留。
- 以 `CARGO_TARGET_DIR=/tmp/claw-target` 运行,可避免容器属主的 `target/` 产物留在你的 bind-mount 检出目录里。
- 非容器本地开发,请继续使用 [`../USAGE.md`](../USAGE.md) 与 [`../rust/README.md`](../rust/README.md)。
