"""Run the analyzer from the terminal: python run_cli.py <csv> "<question>"."""
import asyncio
import sys
from pathlib import Path

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import ToolCallExecutionEvent, ToolCallRequestEvent

from config.settings import WORK_DIR
from teams.runner import run_analysis


async def main(csv_path: str, question: str) -> None:
    async for item in run_analysis(Path(csv_path).read_bytes(), question):
        if isinstance(item, TaskResult):
            print(f"\n=== Finished: {item.stop_reason} ===")
        elif isinstance(item, ToolCallRequestEvent):
            print(f"\n--- [{item.source}] running code ---")
        elif isinstance(item, ToolCallExecutionEvent):
            for res in item.content:
                status = "ERROR" if res.is_error else "ok"
                print(f"--- [{item.source}] execution {status} ---\n{res.content[-1500:]}")
        elif item.source != "user":
            print(f"\n##### {item.source} #####\n{item.to_text()}")
    print("\nOutputs in", WORK_DIR, ":", sorted(p.name for p in WORK_DIR.iterdir()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit('usage: python run_cli.py <csv> "<question>"')
    asyncio.run(main(sys.argv[1], sys.argv[2]))
