> 🌐 本文档由 [ultraworkers/claw-code](https://github.com/ultraworkers/claw-code) 翻译,英文原版见原项目。

# 模型兼容性指南

本文档描述 OpenAI 兼容 provider 中针对特定模型的特殊处理。新增模型或 provider 时,请先查阅本指南,以确保正确的兼容性。

## 目录

- [概览](#概览)
- [模型特殊处理](#模型特殊处理)
  - [Kimi 模型(排除 is_error)](#kimi-模型排除-is_error)
  - [推理模型(剥离调参参数)](#推理模型剥离调参参数)
  - [GPT-5(max_completion_tokens)](#gpt-5max_completion_tokens)
  - [Qwen 与 Kimi 模型(DashScope 路由)](#qwen-与-kimi-模型dashscope-路由)
  - [自定义网关 slug 与 extra_body 参数](#自定义网关-slug-与-extra_body-参数)
- [实现细节](#实现细节)
- [新增模型](#新增模型)
- [测试](#测试)

## 概览

`openai_compat.rs` provider 负责把 Claude Code 的内部消息格式翻译为 OpenAI 兼容的 chat completion 请求。不同模型在以下方面各有差异:

- 工具结果消息字段(`is_error`)
- 采样参数(temperature、top_p 等)
- token 限制字段(`max_tokens` 与 `max_completion_tokens`)
- Base URL 路由
- provider 专属的 extra body 参数(`web_search_options`、`parallel_tool_calls`、本地服务器开关等)
- 面向 status/doctor 界面的 provider 诊断

## 模型特殊处理

### Kimi 模型(排除 is_error)

**受影响模型:** `kimi-k2.5`、`kimi-k1.5`、`kimi-moonshot` 及名称中含 `kimi` 的所有模型(大小写不敏感)

**行为:** 工具结果消息中**排除** `is_error` 字段。

**原因:** Kimi 模型(经 Moonshot AI 与 DashScope)会以 400 Bad Request 拒绝 `is_error` 字段:
```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Unknown field: is_error"
  }
}
```

**检测:**
```rust
fn model_rejects_is_error_field(model: &str) -> bool {
    let lowered = model.to_ascii_lowercase();
    let canonical = lowered.rsplit('/').next().unwrap_or(lowered.as_str());
    canonical.starts_with("kimi")
}
```

**测试:** 见 `openai_compat.rs` 中的 `model_rejects_is_error_field_detects_kimi_models` 及相关测试。

---

### 推理模型(剥离调参参数)

**受影响模型:**
- OpenAI:`o1`、`o1-*`、`o3`、`o3-*`、`o4`、`o4-*`
- xAI:`grok-3-mini`
- 阿里 DashScope:`qwen-qwq-*`、`qwq-*`、`qwen3-*-thinking`

**行为:** 请求中会**剥离**以下调参参数:
- `temperature`
- `top_p`
- `frequency_penalty`
- `presence_penalty`

**原因:** 推理/思维链模型使用固定的采样策略,收到这些参数会报 400 错误。

**例外:** 对兼容模型,显式设置时仍会带上 `reasoning_effort`。

**检测:**
```rust
fn is_reasoning_model(model: &str) -> bool {
    let canonical = model.to_ascii_lowercase()
        .rsplit('/')
        .next()
        .unwrap_or(model);
    canonical.starts_with("o1")
        || canonical.starts_with("o3")
        || canonical.starts_with("o4")
        || canonical == "grok-3-mini"
        || canonical.starts_with("qwen-qwq")
        || canonical.starts_with("qwq")
        || (canonical.starts_with("qwen3") && canonical.contains("-thinking"))
}
```

**测试:** 见 `reasoning_model_strips_tuning_params`、`grok_3_mini_is_reasoning_model`、`qwen_reasoning_variants_are_detected` 测试。

---

### GPT-5(max_completion_tokens)

**受影响模型:** 所有以 `gpt-5` 开头的模型

**行为:** 请求负载中使用 `max_completion_tokens` 而不是 `max_tokens`。

**原因:** GPT-5 模型要求 `max_completion_tokens` 字段;旧版 `max_tokens` 会导致请求校验失败:
```json
{
  "error": {
    "message": "Unknown field: max_tokens"
  }
}
```

**实现:**
```rust
let max_tokens_key = if wire_model.starts_with("gpt-5") {
    "max_completion_tokens"
} else {
    "max_tokens"
};
```

**测试:** 见 `gpt5_uses_max_completion_tokens_not_max_tokens` 与 `non_gpt5_uses_max_tokens` 测试。

---

### Qwen 与 Kimi 模型(DashScope 路由)

**受影响模型:** 所有带 `qwen` 或 `kimi` 前缀的模型,包括 `qwen/`、`qwen-`、`kimi/`、`kimi-` 形式。

**行为:** 路由到 DashScope(`https://dashscope.aliyuncs.com/compatible-mode/v1`),而不是回退到环境凭据对应的 provider。发送上线模型前会剥离已知的路由前缀。

**原因:** Qwen 与 Kimi 兼容模式模型托管在阿里云 DashScope 服务上,不在 OpenAI 或 Anthropic。

**配置:**
```rust
pub const DEFAULT_DASHSCOPE_BASE_URL: &str = "https://dashscope.aliyuncs.com/compatible-mode/v1";
```

**认证:** 使用 `DASHSCOPE_API_KEY` 环境变量。

**注意:** 部分 Qwen 模型同时是推理模型(见上文[推理模型](#推理模型剥离调参参数)),会同时应用两种处理。


---

### 自定义网关 slug 与 extra_body 参数

**受影响模型:** 经 OpenAI 兼容 provider 路由的含斜杠模型 ID,尤其是配置了 `OPENAI_BASE_URL` 的自定义网关,如 OpenRouter、本地路由器或其他 `/v1/chat/completions` 服务。

**行为:**
- 默认 OpenAI API 与本地/私有 OpenAI 兼容 base URL 会把 `openai/` 视为路由前缀,上线发送裸模型名。
- 非本地的自定义 OpenAI 兼容 base URL 会保留 `openai/gpt-4.1-mini` 这类含斜杠 slug,让 OpenRouter 之类的网关收到它们期望的精确模型 ID。本地含斜杠模型 ID 可用 `local/` 前缀,仅剥离这个逃生通道前缀,其余部分原样发送。
- `MessageRequest::extra_body` 在核心字段填充后透传自定义请求 JSON,支持 `web_search_options`、`parallel_tool_calls` 等 provider 专属选项。
- 受保护的核心字段(`model`、`messages`、`stream`、`tools`、`tool_choice`、`max_tokens`、`max_completion_tokens`)无法通过 `extra_body` 覆盖。

**测试:** 见 `openai_compat_integration.rs` 中的 `custom_openai_gateway_preserves_slash_model_ids_and_extra_body_params`,以及 `openai_compat.rs` 中的 `wire_model_strips_openai_prefix_for_default_and_local_preserves_custom_gateways`、`local_routing_prefix_strips_only_escape_hatch`、`extra_body_params_are_passed_through_without_overriding_core_fields`。

## 实现细节

### 文件位置
所有模型专属逻辑位于:
```
rust/crates/api/src/providers/openai_compat.rs
```

### 关键函数

| 函数 | 用途 |
|----------|---------|
| `model_rejects_is_error_field()` | 检测不支持工具结果中 `is_error` 的模型 |
| `is_reasoning_model()` | 检测需要剥离调参参数的推理模型 |
| `translate_message()` | 把内部消息转换为 OpenAI 格式(应用 `is_error` 逻辑) |
| `build_chat_completion_request()` | 构造完整请求负载(应用所有模型专属逻辑与安全的 `extra_body` 透传) |
| `provider_diagnostics_for_model()` | 生成 provider/status 诊断,包括认证/base-url 变量、推理行为、代理支持、extra-body 支持与斜杠模型保留 |

### Provider 前缀处理

所有模型检测函数在匹配前会剥离 provider 前缀(如 `dashscope/kimi-k2.5` → `kimi-k2.5`):

```rust
let canonical = model.to_ascii_lowercase()
    .rsplit('/')
    .next()
    .unwrap_or(model);
```

这保证无论模型名带不带 provider 前缀,检测结果一致。上线模型的处理更细:对 provider 原生默认值会剥离已知路由前缀,而自定义 OpenAI 兼容 base URL 会保留含斜杠的网关 slug。

## 新增模型

新增模型支持时:

1. **判断是否为推理模型**
   - 是否拒绝 temperature/top_p 参数?
   - 加入 `is_reasoning_model()` 检测

2. **检查工具结果兼容性**
   - 是否拒绝 `is_error` 字段?
   - 加入 `model_rejects_is_error_field()` 检测

3. **检查 token 限制字段**
   - 是否要求 `max_completion_tokens` 而非 `max_tokens`?
   - 更新 `max_tokens_key` 逻辑

4. **检查自定义网关行为**
   - 含斜杠 ID 是否应为自定义 `OPENAI_BASE_URL` 网关保留?
   - 该特性应做成类型化请求字段,还是 `extra_body` 透传?

5. **补充测试**
   - 检测函数的单元测试
   - `build_chat_completion_request` 的集成测试

6. **更新本文档**
   - 把模型加入受影响列表
   - 记录任何特殊行为

## 测试

### 运行模型专属测试

```bash
# 全部 OpenAI 兼容性测试
cargo test --package api providers::openai_compat

# 特定测试类别
cargo test --package api model_rejects_is_error_field
cargo test --package api reasoning_model
cargo test --package api gpt5
cargo test --package api qwen
cargo test --package api custom_openai_gateway_preserves_slash_model_ids_and_extra_body_params
cargo test --package api provider_diagnostics_explain_openai_compatible_capabilities
```

### 测试文件

- 单元测试:`rust/crates/api/src/providers/openai_compat.rs`(`mod tests` 内)
- 集成测试:`rust/crates/api/tests/openai_compat_integration.rs`

### 验证模型检测

不发起 API 调用即可验证模型被正确识别:

```rust
#[test]
fn my_new_model_is_detected() {
    // is_error 处理
    assert!(model_rejects_is_error_field("my-model"));
    
    // 推理模型检测
    assert!(is_reasoning_model("my-model"));
    
    // provider 前缀处理
    assert!(model_rejects_is_error_field("provider/my-model"));
}
```

---

*最后更新:2026-05-15*

如有疑问或需要更新,请参见 `rust/crates/api/src/providers/openai_compat.rs` 中的实现。
