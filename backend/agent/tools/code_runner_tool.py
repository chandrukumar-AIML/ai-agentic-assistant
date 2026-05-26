import asyncio
import time
import logging
import re
import traceback
from io import StringIO
from contextlib import redirect_stdout

from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import safe_builtins, guarded_iter_unpack_sequence
from RestrictedPython.PrintCollector import PrintCollector

from backend.agent.state import AgentState  # FIXED: wrong import path
from backend.agent.tools.base_tool import make_tool_result  # FIXED: wrong import path

logger = logging.getLogger(__name__)

EXEC_TIMEOUT_SECONDS = 10

SAFE_GLOBALS = {
    **safe_globals,
    "__builtins__": {
        **safe_builtins,
        "print": print, "range": range, "enumerate": enumerate,
        "zip": zip, "map": map, "filter": filter, "sorted": sorted,
        "reversed": reversed, "sum": sum, "min": min, "max": max,
        "abs": abs, "round": round, "len": len, "list": list,
        "dict": dict, "set": set, "tuple": tuple, "str": str,
        "int": int, "float": float, "bool": bool, "type": type,
    },
    # RestrictedPython compiled code calls _print_(_getattr_) to create
    # a PrintCollector INSTANCE, then calls instance._call_print(x).
    # So _print_ must be the CLASS (factory), _getattr_ must also be provided.
    "_print_":              PrintCollector,
    "_getiter_":              iter,
    "_getattr_":              getattr,
    "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
}


def _make_safe_globals() -> dict:
    """Return a fresh copy of SAFE_GLOBALS for each exec call."""
    return dict(SAFE_GLOBALS)


def _extract_code_block(text: str) -> str:
    match = re.search(r"```(?:python)?\n?(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def _run_sandboxed(code: str) -> tuple[str, str]:
    """
    Execute code in RestrictedPython sandbox (sync — run in thread).
    Returns (stdout_output, error_message).
    noqa: S102 — exec on RestrictedPython-compiled bytecode only; intentional.
    """
    try:
        byte_code = compile_restricted(code, filename="<agent>", mode="exec")
    except SyntaxError as e:
        return "", f"SyntaxError: {e}"

    stdout_buffer = StringIO()
    local_vars: dict = {}

    # Each exec call gets its own dict copy so _print_ state is isolated.
    exec_globals = _make_safe_globals()

    try:
        with redirect_stdout(stdout_buffer):
            exec(byte_code, exec_globals, local_vars)  # noqa: S102

        # RestrictedPython's compiled code stores the PrintCollector INSTANCE
        # in local_vars under the key '_print' (NO trailing underscore).
        # _print_._call_print(x) → print(x, file=_print) → _print.write(str)
        # → _print.txt.append(str).  Read from there.
        printer = local_vars.get("_print")
        if hasattr(printer, "txt"):
            # txt is a list of str chunks
            collected = "".join(printer.txt) if isinstance(printer.txt, list) else str(printer.txt)
        else:
            collected = ""

        raw_stdout = stdout_buffer.getvalue()
        output = (collected + raw_stdout).strip()
        return output, ""
    except Exception:
        return stdout_buffer.getvalue(), traceback.format_exc(limit=5)


async def code_executor_node(state: AgentState) -> dict:
    start = time.monotonic()
    raw_code = _extract_code_block(state["user_query"])

    if not raw_code or len(raw_code) < 3:
        result = make_tool_result(
            tool_name="code_runner_tool",
            content="No executable code found in the query.",
            confidence=0.1,
        )
    else:
        try:
            # _run_sandboxed is CPU-bound — run in thread to avoid blocking event loop
            output, error = await asyncio.wait_for(
                asyncio.to_thread(_run_sandboxed, raw_code),
                timeout=EXEC_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            output, error = "", f"Execution timed out after {EXEC_TIMEOUT_SECONDS} seconds."

        if error:
            content = f"Code execution error:\n{error}"
            confidence = 0.2
        elif output:
            content = f"Output:\n{output}"
            confidence = 0.95
        else:
            content = "Code ran successfully with no output."
            confidence = 0.7

        result = make_tool_result(
            tool_name="code_runner_tool",
            content=content,
            source="sandbox_exec",
            confidence=confidence,
            metadata={"code": raw_code[:500], "error": error or None},
        )

    elapsed = (time.monotonic() - start) * 1000

    return {
        "tool_results": state.get("tool_results", []) + [result],
        "latency_ms":   {"code_executor": round(elapsed, 2)},
    }