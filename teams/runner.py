"""Runs one analysis end to end: temp storage -> Docker sandbox -> agent team."""
import shutil
from typing import AsyncGenerator

from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage

from config.docker_executor import get_docker_executor
from config.model_client import get_model_client
from config.settings import DATA_FILENAME, WORK_DIR
from teams.analyzer_team import build_task, build_team


def reset_work_dir(csv_bytes: bytes) -> None:
    """Clear outputs from the previous run and store the uploaded CSV."""
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    WORK_DIR.mkdir(parents=True)
    (WORK_DIR / DATA_FILENAME).write_bytes(csv_bytes)


async def run_analysis(
    csv_bytes: bytes, question: str
) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | TaskResult, None]:
    reset_work_dir(csv_bytes)
    model_client = get_model_client()
    executor = get_docker_executor()
    await executor.start()
    try:
        team = build_team(model_client, executor)
        async for item in team.run_stream(task=build_task(question)):
            yield item
    finally:
        await executor.stop()
        await model_client.close()
