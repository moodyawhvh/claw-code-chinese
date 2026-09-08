<div align="center">

# claw-code 中文翻译版

**[中文版] claw-code — 由 AI 代理自动打理的 Rust CLI 代理框架"博物馆展品"**

[![原项目](https://img.shields.io/badge/原项目-ultraworkers--claw-code-blue?style=flat-square&logo=github)](https://github.com/ultraworkers/claw-code)
[![中文文档](https://img.shields.io/badge/中文文档-README.zh--CN.md-orange?style=flat-square)](README.zh-CN.md)
[![GitHub Stars](https://img.shields.io/github/stars/ultraworkers/claw-code?style=flat-square&label=原项目Stars)](https://github.com/ultraworkers/claw-code/stargazers)
[![微信联系](https://img.shields.io/badge/微信-uaycar-brightgreen?style=flat-square&logo=wechat)](#)

</div>

---

> 这是 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 的中文翻译版本。
> 完整源代码请访问原项目:https://github.com/ultraworkers/claw-code

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

---

## 📖 项目简介

Claw Code 是 `claw` CLI 代理框架(agent harness)的公开 Rust 实现,定位颇为特别:它不是传统的产品型仓库,而是一座**由 AI 代理管理的"博物馆展品"**——由上游的 LazyCodex、Gajae-Code 等 harness 负责规划、执行、验证、打标签和持续维护。项目核心是 `claw` 命令行工具,支持多模型 Provider 接入、交互式会话、健康自检等能力,并采用 MIT 许可证开源。

## ✨ 主要特性

- 🦀 **纯 Rust 实现**:规范代码位于 `rust/` 工作区,提供 `claw` CLI 二进制
- 🤖 **代理自主维护**:仓库由 harness 代理自动清扫、标注与维护,是"代理管理展品"的实验性样本
- 🔌 **多 Provider 认证**:支持 `ANTHROPIC_API_KEY`、`OPENAI_API_KEY` 等多种 API Key(不支持 Claude 订阅登录)
- 🩺 **`claw doctor` 健康检查**:一条命令验证 API Key、模型访问与工具配置
- 💬 **交互式会话 + 单次执行**:`claw` 进入交互模式,`claw prompt "..."` 直接运行提示词
- 🪟 **Windows / PowerShell 一等支持**:提供 PowerShell 优先的安装文档与发布包说明
- 🧪 **Parity 对照测试**:附带确定性 mock 服务的 parity harness,跟踪 Rust 移植进度
- 📚 **完善文档体系**:USAGE、ROADMAP、PHILOSOPHY、容器化工作流、本地 OpenAI 兼容模型接入指南等
- 📄 **MIT 许可证**:代码完全开源,可自由使用与修改

## 📁 文件说明

| 文件 | 说明 |
|:-----|:-----|
| README.md | 本文件(中文简介) |
| README.zh-CN.md | 详细中文文档(完整汉化) |

## 🚀 快速开始

> ⚠️ **注意:不要执行 `cargo install claw-code`**——crates.io 上的 `claw-code` 是已废弃的占位包。本仓库仅支持从源码构建,步骤如下:

```bash
# 1. 克隆并构建
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace

# 2. 设置 API Key(Anthropic API Key,非 Claude 订阅)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. 验证环境是否就绪
./target/debug/claw doctor

# 4. 运行一条提示词
./target/debug/claw prompt "say hello"

# 5. 启动交互式会话
./target/debug/claw
```

Windows(PowerShell)用户:二进制名为 `claw.exe`,可用 `.\target\debug\claw.exe` 或直接 `cargo run -- prompt "say hello"`。

更多安装细节、Windows 配置、PATH 设置与故障排查,请阅读 [README.zh-CN.md](README.zh-CN.md)。

完整源代码与最新版本请访问原项目:https://github.com/ultraworkers/claw-code

## 📞 联系方式

**代部署 / 定制服务 / 技术咨询 请添加微信:uaycar**

---

本项目为 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 的中文翻译版本,所有代码版权归原项目作者所有,遵循其原始许可证。

**如果觉得有用,请给原项目点个 Star!** ⭐
