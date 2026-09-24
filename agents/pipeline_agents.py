from autogen_agentchat.agents import AssistantAgent
from autogen_core.code_executor import CodeExecutor
from autogen_core.models import ChatCompletionClient

from agents import prompts
from agents.code_tool import build_code_tool
from config.settings import DATA_FILENAME, MAX_TOOL_ITERATIONS, WORK_DIR

# (name, description, system prompt, input file, output file) in pipeline order.
# The input/output files let the CodeExecutor tool validate each stage's result.
AGENT_SPECS = [
    ("DataLoader", "Loads and profiles the uploaded CSV.", prompts.DATA_LOADER, DATA_FILENAME, "profile.md"),
    ("DataCleaner", "Cleans the dataset.", prompts.DATA_CLEANER, DATA_FILENAME, "cleaned_data.csv"),
    ("FeatureEngineer", "Creates features.", prompts.FEATURE_ENGINEER, "cleaned_data.csv", "featured_data.csv"),
    ("DataAnalyzer", "Computes statistics that answer the question.", prompts.DATA_ANALYZER, None, "analysis.md"),
    ("Visualizer", "Creates PNG charts of the findings.", prompts.VISUALIZER, None, None),
    ("ReportGenerator", "Writes the final report and terminates.", prompts.REPORT_GENERATOR, None, "report.md"),
]


def build_pipeline_agents(
    model_client: ChatCompletionClient, executor: CodeExecutor
) -> list[AssistantAgent]:
    """Create the six AI agents; each gets a CodeExecutor tool on the shared Docker sandbox."""
    return [
        AssistantAgent(
            name=name,
            description=description,
            system_message=system_message,
            model_client=model_client,
            tools=[build_code_tool(executor, WORK_DIR, input_file, output_file)],
            reflect_on_tool_use=True,
            max_tool_iterations=MAX_TOOL_ITERATIONS,
        )
        for name, description, system_message, input_file, output_file in AGENT_SPECS
    ]
