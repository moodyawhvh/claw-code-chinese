# =============================================================================
# src/runtime.py —— Python 移植工作区的最小 "runtime" 门面。
#
# 提供:
#   * PortRuntime.route_prompt:把 prompt 按词法打分路由到镜像的命令/工具清单;
#   * PortRuntime.bootstrap_session:拼装一次模拟运行的完整会话快照
#     (上下文 + 环境安装报告 + 路由命中 + 命令/工具执行 + 流事件 + 持久化路径);
#   * PortRuntime.run_turn_loop:小型的有状态多轮循环。
#
# 仅用于移植/一致性演示,不含真实 LLM 调用;权威实现在 rust/ workspace。
# =============================================================================
from __future__ import annotations

from dataclasses import dataclass

from .commands import PORTED_COMMANDS, get_command
from .context import PortContext, build_port_context, render_context
from .history import HistoryLog
from .models import PermissionDenial, PortingModule
from .query_engine import QueryEngineConfig, QueryEnginePort, TurnResult
from .setup import SetupReport, WorkspaceSetup, run_setup
from .system_init import build_system_init_message
from .tools import PORTED_TOOLS
from .execution_registry import build_execution_registry


@dataclass(frozen=True)
class RoutedMatch:
    """单条路由命中:kind 为 'command' 或 'tool',score 为词法匹配得分。"""
    kind: str
    name: str
    source_hint: str
    score: int


@dataclass
class RuntimeSession:
    """一次模拟 runtime 会话的完整快照,可整体渲染为 Markdown 报告。"""
    prompt: str
    context: PortContext
    setup: WorkspaceSetup
    setup_report: SetupReport
    system_init_message: str
    history: HistoryLog
    routed_matches: list[RoutedMatch]
    turn_result: TurnResult
    command_execution_messages: tuple[str, ...]
    tool_execution_messages: tuple[str, ...]
    stream_events: tuple[dict[str, object], ...]
    persisted_session_path: str

    def as_markdown(self) -> str:
        lines = [
            '# Runtime Session',
            '',
            f'Prompt: {self.prompt}',
            '',
            '## Context',
            render_context(self.context),
            '',
            '## Setup',
            f'- Python: {self.setup.python_version} ({self.setup.implementation})',
            f'- Platform: {self.setup.platform_name}',
            f'- Test command: {self.setup.test_command}',
            '',
            '## Startup Steps',
            *(f'- {step}' for step in self.setup.startup_steps()),
            '',
            '## System Init',
            self.system_init_message,
            '',
            '## Routed Matches',
        ]
        if self.routed_matches:
            lines.extend(
                f'- [{match.kind}] {match.name} ({match.score}) — {match.source_hint}'
                for match in self.routed_matches
            )
        else:
            lines.append('- none')
        lines.extend([
            '',
            '## Command Execution',
            *(self.command_execution_messages or ('none',)),
            '',
            '## Tool Execution',
            *(self.tool_execution_messages or ('none',)),
            '',
            '## Stream Events',
            *(f"- {event['type']}: {event}" for event in self.stream_events),
            '',
            '## Turn Result',
            self.turn_result.output,
            '',
            f'Persisted session path: {self.persisted_session_path}',
            '',
            self.history.as_markdown(),
        ])
        return '\n'.join(lines)


class PortRuntime:
    """镜像 runtime 的核心门面:prompt 路由、会话引导与多轮循环。"""

    def route_prompt(self, prompt: str, limit: int = 5) -> list[RoutedMatch]:
        """把 prompt 路由到命令/工具清单。

        规则:显式斜杠命令('/xxx')优先且去重;command 与 tool 各保底取一条;
        其余按 (score 降序, kind, name) 排序补足到 limit。
        """
        explicit_command = self._explicit_command_match(prompt)
        tokens = {token.lower() for token in prompt.replace('/', ' ').replace('-', ' ').split() if token}
        by_kind = {
            'command': self._collect_matches(tokens, PORTED_COMMANDS, 'command'),
            'tool': self._collect_matches(tokens, PORTED_TOOLS, 'tool'),
        }

        selected: list[RoutedMatch] = []
        if explicit_command is not None:
            selected.append(explicit_command)
            by_kind['command'] = [
                match
                for match in by_kind['command']
                if not (
                    match.name == explicit_command.name
                    and match.source_hint == explicit_command.source_hint
                )
            ]
        for kind in ('command', 'tool'):
            if by_kind[kind]:
                selected.append(by_kind[kind].pop(0))

        leftovers = sorted(
            [match for matches in by_kind.values() for match in matches],
            key=lambda item: (-item.score, item.kind, item.name),
        )
        selected.extend(leftovers[: max(0, limit - len(selected))])
        return selected[:limit]

    @staticmethod
    def _explicit_command_match(prompt: str) -> RoutedMatch | None:
        """识别 prompt 首个 token 是否为显式斜杠命令;命中则返回固定 100 分的匹配。"""
        first_token = prompt.strip().split(maxsplit=1)[0] if prompt.strip() else ''
        command_name = first_token.removeprefix('/')
        if not command_name:
            return None
        module = get_command(command_name)
        if module is None:
            return None
        return RoutedMatch(
            kind='command',
            name=module.name,
            source_hint=module.source_hint,
            score=100,
        )

    def bootstrap_session(self, prompt: str, limit: int = 5) -> RuntimeSession:
        """引导一次完整模拟会话:环境安装 → 路由 → 执行命令/工具 shim →
        推断权限拒绝 → 流式与整轮提交 → 持久化 → 写入历史日志。"""
        context = build_port_context()
        setup_report = run_setup(trusted=True)
        setup = setup_report.setup
        history = HistoryLog()
        engine = QueryEnginePort.from_workspace()
        history.add('context', f'python_files={context.python_file_count}, archive_available={context.archive_available}')
        history.add('registry', f'commands={len(PORTED_COMMANDS)}, tools={len(PORTED_TOOLS)}')
        matches = self.route_prompt(prompt, limit=limit)
        registry = build_execution_registry()
        command_execs = tuple(registry.command(match.name).execute(prompt) for match in matches if match.kind == 'command' and registry.command(match.name))
        tool_execs = tuple(registry.tool(match.name).execute(prompt) for match in matches if match.kind == 'tool' and registry.tool(match.name))
        denials = tuple(self._infer_permission_denials(matches))
        stream_events = tuple(engine.stream_submit_message(
            prompt,
            matched_commands=tuple(match.name for match in matches if match.kind == 'command'),
            matched_tools=tuple(match.name for match in matches if match.kind == 'tool'),
            denied_tools=denials,
        ))
        turn_result = engine.submit_message(
            prompt,
            matched_commands=tuple(match.name for match in matches if match.kind == 'command'),
            matched_tools=tuple(match.name for match in matches if match.kind == 'tool'),
            denied_tools=denials,
        )
        persisted_session_path = engine.persist_session()
        history.add('routing', f'matches={len(matches)} for prompt={prompt!r}')
        history.add('execution', f'command_execs={len(command_execs)} tool_execs={len(tool_execs)}')
        history.add('turn', f'commands={len(turn_result.matched_commands)} tools={len(turn_result.matched_tools)} denials={len(turn_result.permission_denials)} stop={turn_result.stop_reason}')
        history.add('session_store', persisted_session_path)
        return RuntimeSession(
            prompt=prompt,
            context=context,
            setup=setup,
            setup_report=setup_report,
            system_init_message=build_system_init_message(trusted=True),
            history=history,
            routed_matches=matches,
            turn_result=turn_result,
            command_execution_messages=command_execs,
            tool_execution_messages=tool_execs,
            stream_events=stream_events,
            persisted_session_path=persisted_session_path,
        )

    def run_turn_loop(self, prompt: str, limit: int = 5, max_turns: int = 3, structured_output: bool = False) -> list[TurnResult]:
        """跑一个有状态的多轮循环:第 1 轮用原始 prompt,
        后续轮追加 ' [turn N]' 标记;一旦某轮 stop_reason 非 'completed' 即提前终止。"""
        engine = QueryEnginePort.from_workspace()
        engine.config = QueryEngineConfig(max_turns=max_turns, structured_output=structured_output)
        matches = self.route_prompt(prompt, limit=limit)
        command_names = tuple(match.name for match in matches if match.kind == 'command')
        tool_names = tuple(match.name for match in matches if match.kind == 'tool')
        results: list[TurnResult] = []
        for turn in range(max_turns):
            turn_prompt = prompt if turn == 0 else f'{prompt} [turn {turn + 1}]'
            result = engine.submit_message(turn_prompt, command_names, tool_names, ())
            results.append(result)
            if result.stop_reason != 'completed':
                break
        return results

    def _infer_permission_denials(self, matches: list[RoutedMatch]) -> list[PermissionDenial]:
        """权限拒绝推断:Python 移植版仍对 bash 类工具保持门禁(模拟只读安全策略)。"""
        denials: list[PermissionDenial] = []
        for match in matches:
            if match.kind == 'tool' and 'bash' in match.name.lower():
                denials.append(PermissionDenial(tool_name=match.name, reason='destructive shell execution remains gated in the Python port'))
        return denials

    def _collect_matches(self, tokens: set[str], modules: tuple[PortingModule, ...], kind: str) -> list[RoutedMatch]:
        """对给定模块集合逐个打分,收集得分 > 0 的命中并按 (score 降序, name) 排序。"""
        matches: list[RoutedMatch] = []
        for module in modules:
            score = self._score(tokens, module)
            if score > 0:
                matches.append(RoutedMatch(kind=kind, name=module.name, source_hint=module.source_hint, score=score))
        matches.sort(key=lambda item: (-item.score, item.name))
        return matches

    @staticmethod
    def _score(tokens: set[str], module: PortingModule) -> int:
        """词法打分:token 出现在模块名/来源提示/职责描述(小写)中则各计 1 分。"""
        haystacks = [module.name.lower(), module.source_hint.lower(), module.responsibility.lower()]
        score = 0
        for token in tokens:
            if any(token in haystack for haystack in haystacks):
                score += 1
        return score
