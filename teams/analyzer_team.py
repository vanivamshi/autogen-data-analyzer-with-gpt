from autogen_agentchat.conditions import MaxMessageTermination, SourceMatchTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.code_executor import CodeExecutor
from autogen_core.models import ChatCompletionClient

from agents import build_pipeline_agents
from config.settings import DATA_FILENAME, MAX_MESSAGES, TERMINATION_WORD


def build_team(model_client: ChatCompletionClient, executor: CodeExecutor) -> RoundRobinGroupChat:
    agents = build_pipeline_agents(model_client, executor)
    # One pass through the pipeline: stop after ReportGenerator's turn (or when it says
    # TERMINATE), so the round-robin never wraps around; the message cap is a safety net.
    termination = (
        TextMentionTermination(TERMINATION_WORD, sources=["ReportGenerator"])
        | SourceMatchTermination(["ReportGenerator"])
        | MaxMessageTermination(MAX_MESSAGES)
    )
    return RoundRobinGroupChat(agents, termination_condition=termination)


def build_task(question: str) -> str:
    return (
        f"The user uploaded a dataset saved as `{DATA_FILENAME}` in the working directory.\n"
        f"User question: {question}\n\n"
        "Work through the pipeline: DataLoader -> DataCleaner -> FeatureEngineer -> "
        "DataAnalyzer -> Visualizer -> ReportGenerator. Each agent does only its own stage."
    )
