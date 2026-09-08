> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。(原文为俄语版本,本译稿由俄语原稿译出。)

# Claw Code 项目概念

本文档记录 **Claw Code** 仓库的**目标**、**架构**与**原则**——即 CLI agent **`claw`** 及配套工具的公开 Rust 实现。代码库的事实来源为 [`rust/`](rust/README.md) 目录下的 workspace;操作场景见 [`USAGE.md`](USAGE.md) 与 [`how_to_run.md`](how_to_run.md)(claw-analog);想法积压见 [`futute.md`](futute.md)。

独立产品线"从 CLI → 到个人助手"(频道/记忆/工具/主动性/会话)在 [`docs/personal-assistant-roadmap.md`](docs/personal-assistant-roadmap.md) 中描述。

---

## 1. 产品定位

**Claw Code** 是:

1. **主 CLI `claw`**(`rusty-claude-cli`):功能完整的 agent,带 REPL、OAuth、扩展工具集(包括 bash、MCP、插件等)、流式输出,并与 **Anthropic**、**OpenAI 兼容** API 及 **xAI** 等 provider 集成。
2. **`claw-analog`** —— 构建在**同一 API 层**(`api` crate)之上的轻量外壳:窄而可预测的工具集,仅限操作 workspace 文件系统,权限模式显式,适用于 **CI**、**脚本**和**外部 agent**(NDJSON)。
3. **`claw-rag-service`** —— 独立进程:对仓库做**索引**(分块 + 嵌入向量存入 SQLite),提供语义检索的 **HTTP API**,以及用于人工检查索引的最小**网页 UI**。

总体思路:提供一种**安全**、**可审计**且**可复现**的方式,让 LLM 作用于代码与文档,并保留从最小 harness 演化到完整 `claw` 的路径。

---

## 2. 目标用户与场景

| 用户群 | 任务 |
|---------|--------|
| 开发者 | 通过完整 `claw` 日常处理代码库:REPL、工具、会话。 |
| 自动化作者 | 一次性 prompt、`--output-format json` 管道、不带 bash 的内嵌 agent。 |
| 运维 / 审计 | `claw-analog` **read-only** + **audit** 预设;显式限制与策略。 |
| 移植与一致性 | 与参照实现比对行为(`PARITY.md`、mock-harness)。 |
| 单仓之上的 RAG | 独立的 `ingest` + `serve`;agent 在设置 `RAG_BASE_URL` 后通过 **`retrieve_context`** 接入上下文。 |

---

## 3. 架构(逻辑视图)

```text
                    ┌─────────────────────────────────────┐
                    │  Provider(Anthropic / OpenAI / …)   │
                    └─────────────────┬───────────────────┘
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       │                              │                              │
       ▼                              ▼                              ▼
┌──────────────┐              ┌──────────────┐              ┌──────────────────┐
│  rusty-      │              │  claw-analog │              │ claw-rag-service │
│  claude-cli  │              │  (lean loop) │              │ HTTP + SQLite    │
│  («claw»)    │              │              │              │ ingest / query   │
└──────┬───────┘              └──────┬───────┘              └────────┬─────────┘
       │                              │                               │
       │          crates/api          │         retrieve_context      │
       │    runtime, tools, …         │         (POST /v1/query)      │
       └──────────────┬───────────────┴───────────────────────────────┘
                      │
                      ▼
               文件系统 / workspace(-w)
```

**分离原则:** 重量级的索引与嵌入向量存储**不**塞进 `claw-analog`,而是放在 **`claw-rag-service`** 中。agent 只通过 HTTP 调用检索——这样更容易扩容、更换向量库,也能隔离嵌入服务的密钥。

---

## 4. 设计原则

1. **默认安全** —— 相对路径、禁止 `..`、校验是否越出 canonical workspace;`PermissionMode` 与完整 CLI 保持一致;非交互模式下,危险模式在没有显式旗标时会被阻止。
2. **显式限制** —— 读取大小、回合数、glob/grep 上限、RAG 超时;失败是可预期的,而不是"OOM 或死循环"。
3. **面向 agent 的可观测性** —— `run_start` 携带 `schema` 与 `format_version` 的 NDJSON,结构化的 `tool_result`。
4. **模块化** —— 共享的 `api` 提供 provider 接入;`claw-analog` 不复制 RAG 密钥栈,只保留指向服务的 HTTP 客户端。
5. **一致性与测试** —— mock Anthropic、harness 场景、为关键 crate 设立独立 CI job。
6. **文档贴近代码** —— `how_to_run.md`、`docs/rag-web-ui.md`、`docs/container.md` 等。

---

## 5. Workspace 组件(简述)

- **`rusty-claude-cli`** —— 主二进制 **`claw`**:面向用户的全功能产品。
- **`api`** —— provider 客户端、流式输出、请求/响应类型。
- **`runtime`** —— 会话、配置、**PermissionPolicy** / **PermissionEnforcer**、prompt、MCP 等。
- **`tools`** —— 完整 CLI 的内置工具。
- **`claw-analog`** —— 最小循环:读/搜索/写工具(视模式而定)、流式与 JSON 输出、TOML 配置、会话、doctor、config validate、在配置 `RAG_BASE_URL` / `rag_base_url` 时支持 **`retrieve_context`**。
- **`claw-rag-service`** —— `ingest`、`serve`,路由 `/`、`/health`、`/v1/stats`、`/v1/query`;SQLite + OpenAI 兼容嵌入(测试可用 mock)。
- **`mock-anthropic-service`**、**`compat-harness`** 等 —— 可复现性与迁移。

详细分布见 [`rust/README.md`](rust/README.md)。

---

## 6. claw-analog:角色与边界

**目标:** 提供一个"带工具的 agent",同时不扩大攻击面(基础场景中没有任意 shell)。

**工具(概念上):** 读取与遍历目录树(`read_file`、`list_dir`、`glob_workspace`)、字面量搜索(`grep_workspace` / `grep_search`)、可选的 `write_file`,以及可选的对接 RAG 服务的 **`retrieve_context`**。

**最小设计中不包含:** MCP、插件、bash——这些属于**完整 `claw`** 的领域。

---

## 7. RAG 服务:角色与演进

**现状(MVP):** `ingest` 时全量重建索引,向量存 SQLite,检索为全量分块的线性余弦相似度;适合中等规模的代码量。

**演进方向(概念):** 增量索引、ANN(sqlite-vec,Docker 中的 Qdrant/Chroma)、嵌入请求的限流。`GET /` 上的网页 UI 是辅助性的;更高级的 UI 与鉴权按需推进。

细节见 [`docs/rag-web-ui.md`](docs/rag-web-ui.md)。

---

## 8. 主 runtime 之外的仓库内容

- **`src/`**、**`tests/`**(Python 等)为辅助/实验性产物;**权威 runtime** 是 **`rust/`**。
- 文档 **PHILOSOPHY.md**、**ROADMAP.md**、**PARITY.md** 从流程与社区/维护者意图的角度补充本概念文档。

---

## 9. 相邻概念(不属于 Claw Code 核心)

**`docs/`** 中可能存放面向**其他**产品的可移植笔记(例如 NestJS 应用的本地 vision)——它们**不**定义 `claw` 的强制行为,只反映贡献者的相邻兴趣。

---

## 10. 总结

**Claw Code** 是围绕 agent **`claw`** 的 **Rust** 生态:面向开发者的完整 CLI、作为可控最小 agent 的 **`claw-analog`**(面向自动化),以及为代码语义检索服务的**独立 RAG 服务**。项目依赖**显式权限**、**限制**、**可测试性**,以及 agent 与重型索引之间**清晰的 HTTP 边界**。

---

*关键产品决策变化时请更新本文件;详细的功能清单与 backlog 见 [`futute.md`](futute.md)。*

> 注:本文件超过 10000 字符,按预算以核心章节为主翻译,架构图与配置示例保持原样,已覆盖原文全部章节。
