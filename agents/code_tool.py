"""The CodeExecutor tool: runs agent-written Python in the Docker sandbox."""
from pathlib import Path

import pandas as pd
from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock, CodeExecutor
from autogen_core.tools import FunctionTool

MAX_OUTPUT_CHARS = 6000


def _normalize(code: str) -> str:
    """Undo the two JSON-escaping mistakes small models make when sending code."""
    # 1) Whole script on one line with literal "\n" escapes.
    if "\n" not in code.strip() and "\\n" in code:
        code = code.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
    # 2) A "\n" inside a string literal was decoded into a real line break,
    #    leaving an unterminated string: rejoin the line with an escaped "\n".
    for _ in range(200):
        try:
            compile(code, "<agent>", "exec")
            break
        except SyntaxError as err:
            lines = code.split("\n")
            if "unterminated" not in (err.msg or "") or not err.lineno or err.lineno >= len(lines):
                break
            i = err.lineno - 1
            lines[i : i + 2] = [lines[i] + "\\n" + lines[i + 1]]
            code = "\n".join(lines)
    return code


def _check_stage_output(work_dir: Path, input_file: str | None, output_file: str | None) -> str | None:
    """Return a problem description if the stage's output file is missing or damaged."""
    if not output_file:
        return None
    out_path = work_dir / output_file
    if not out_path.exists():
        return f"`{output_file}` was not created. Your script must save it."
    if not (input_file and output_file.endswith(".csv")):
        return None
    try:
        before = pd.read_csv(work_dir / input_file, low_memory=False)
        after = pd.read_csv(out_path, low_memory=False)
    except Exception as exc:
        return f"`{output_file}` could not be read back with pd.read_csv: {exc}"
    if after.empty:
        return f"`{output_file}` has no rows."
    wiped = [
        f"{col} (non-null {before[col].notna().mean():.0%} -> {after[col].notna().mean():.0%})"
        for col in before.columns.intersection(after.columns)
        if before[col].notna().mean() >= 0.5 and after[col].notna().mean() < 0.5
    ]
    if wiped:
        return (
            "Your script turned these columns mostly into NaN: " + ", ".join(wiped) + ". "
            "Probably pd.to_numeric(errors='coerce') on a text column or a .map() that "
            "missed values. Fix the script so these columns keep their data, then re-save."
        )
    return None


def build_code_tool(
    executor: CodeExecutor, work_dir: Path, input_file: str | None = None, output_file: str | None = None
) -> FunctionTool:
    """Create a CodeExecutor tool that also validates the calling stage's output file."""

    async def run_python(code: str) -> str:
        """Run a complete, self-contained Python script in the sandbox and return its printed output.
        Each call is a fresh process: re-import libraries and re-load files every time."""
        result = await executor.execute_code_blocks(
            [CodeBlock(code=_normalize(code), language="python")], CancellationToken()
        )
        output = result.output.strip()[-MAX_OUTPUT_CHARS:] or "(no output — use print() to see results)"
        # Raising marks the tool result as an error so the agent knows to fix and retry.
        if result.exit_code != 0:
            raise RuntimeError(f"exit code {result.exit_code}\n{output}")
        problem = _check_stage_output(work_dir, input_file, output_file)
        if problem:
            raise RuntimeError(f"Script ran, but the stage output is invalid: {problem}\n\nOutput:\n{output}")
        return output

    return FunctionTool(run_python, name="CodeExecutor", description=run_python.__doc__)
