# AutoGen Data Analyzer GPT

Upload a CSV, ask a question in plain English, and a team of AutoGen agents (GPT-4o-mini) loads, cleans, engineers features, analyzes, charts, and reports on your data. All generated code runs in a Docker sandbox.

## Architecture

```
User ──upload CSV/query──▶ Streamlit (app.py)
                               │
                 ┌─────────── AutoGen orchestration ───────────┐
                 │ RoundRobinGroupChat  ──check──▶ TextMentionTermination("TERMINATE")
                 │                                               │
                 │ DataLoader → DataCleaner → FeatureEngineer →  │
                 │ DataAnalyzer → Visualizer → ReportGenerator   │
                 └───────────────┬───────────────────────────────┘
                                 │ run code (CodeExecutor tool)
                                 ▼
             Docker (amancevice/pandas:2.2.2 + matplotlib/seaborn)
                                 │ save PNG / CSV / MD
                                 ▼
                         temp/  (bind-mounted)  ──▶ final report + charts in Streamlit
```

Each agent runs code in a fresh process, so stages pass work through files in `temp/`:
`data.csv → cleaned_data.csv → featured_data.csv → analysis.md → chart_*.png → report.md`.

## Project layout

| Path | Purpose |
|---|---|
| `app.py` | Streamlit UI; streams agent messages, code, and outputs |
| `agents/prompts.py` | System prompt for each agent |
| `agents/pipeline_agents.py` | Builds the 6 `AssistantAgent`s sharing one `CodeExecutor` tool |
| `teams/analyzer_team.py` | `RoundRobinGroupChat` + termination conditions |
| `teams/runner.py` | Resets temp storage, starts/stops Docker, streams the run |
| `config/` | Settings, OpenAI client, Docker executor |
| `docker/Dockerfile` | Sandbox image (auto-built on first run) |
| `agents/code_tool.py` | CodeExecutor tool: runs code in Docker, repairs and validates it |
| `run_cli.py` | Run an analysis from the terminal |
| `sample_data/` | Example datasets |

## Setup

Requires Python 3.10+ and Docker running (your user must be able to run `docker`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your OPENAI_API_KEY in .env
streamlit run app.py
```

The first run builds the `autogen-data-analyzer:latest` image, which takes about a minute. To build it ahead of time:

```bash
docker build -t autogen-data-analyzer:latest docker/
```

## Try it

Sample datasets:
- `sample_data/customer_churn.csv`: 508 rows, deliberately messy (duplicates, missing ages, blank `total_charges`, mixed-case gender, outliers). Ask: "What factors drive customer churn, and which customer segments are most at risk?"
- `sample_data/sales.csv`: ask "Which region and product drive the most revenue, and how does revenue trend by month?"

From the terminal, without the UI:

```bash
python run_cli.py sample_data/customer_churn.csv "What factors drive customer churn?"
```

Outputs (`report.md`, `chart_*.png`, intermediate CSVs) are written to `temp/`.

## Guardrails

`agents/code_tool.py` makes small models like gpt-4o-mini reliable enough:
- It repairs code whose newlines were mangled by JSON escaping.
- It marks non-zero exit codes as tool errors, so the agent retries.
- It checks each stage's output file: the file must exist, and a cleaned or featured CSV may not turn a column mostly into NaN. If a check fails, the agent must fix its script.
- The team stops after one pass, when ReportGenerator finishes.
