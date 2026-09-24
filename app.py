"""Streamlit frontend: upload a CSV, ask a question, watch the agents work."""
import asyncio
import json

import pandas as pd
import streamlit as st
from autogen_agentchat.base import TaskResult
from autogen_agentchat.messages import (
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
)

from config.settings import OPENAI_API_KEY, TERMINATION_WORD, WORK_DIR
from teams.runner import run_analysis

AGENT_AVATARS = {
    "user": "🧑",
    "DataLoader": "📥",
    "DataCleaner": "🧹",
    "FeatureEngineer": "⚙️",
    "DataAnalyzer": "📊",
    "Visualizer": "🖼️",
    "ReportGenerator": "📝",
}

st.set_page_config(page_title="AutoGen Data Analyzer", page_icon="📊", layout="wide")
st.title("📊 AutoGen Data Analyzer GPT")
st.caption("Upload a CSV and ask a question. Six AutoGen agents analyze it in a Docker sandbox.")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY is not set. Copy `.env.example` to `.env` and add your key.")
    st.stop()

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded is not None:
    try:
        st.dataframe(pd.read_csv(uploaded).head(20), use_container_width=True)
    except Exception as exc:  # preview only; agents will try harder to parse it
        st.warning(f"Could not preview file: {exc}")
    uploaded.seek(0)

question = st.chat_input("Ask a question about your data…", disabled=uploaded is None)


def render(item) -> None:
    """Render one streamed team event in the chat."""
    if isinstance(item, TaskResult):
        st.info(f"Finished: {item.stop_reason}")
        return
    source = getattr(item, "source", "")
    avatar = AGENT_AVATARS.get(source, "🤖")
    if isinstance(item, ToolCallRequestEvent):
        with st.chat_message(source, avatar=avatar):
            for call in item.content:
                with st.expander(f"**{source}** → code", expanded=False):
                    try:
                        st.code(json.loads(call.arguments).get("code", call.arguments), language="python")
                    except Exception:
                        st.code(call.arguments)
    elif isinstance(item, ToolCallExecutionEvent):
        with st.chat_message(source, avatar="🐳"):
            for res in item.content:
                label = "❌ execution error" if res.is_error else "✅ execution output"
                with st.expander(f"{label} ({source})", expanded=res.is_error):
                    st.code(res.content[-4000:])
    elif isinstance(item, (TextMessage, ToolCallSummaryMessage)):
        if source == "user":
            return
        with st.chat_message(source, avatar=avatar):
            st.markdown(f"**{source}**")
            st.markdown(item.content.replace(TERMINATION_WORD, "").strip())


async def run_and_render(csv_bytes: bytes, prompt: str) -> None:
    async for item in run_analysis(csv_bytes, prompt):
        render(item)


def show_outputs() -> None:
    charts = sorted(WORK_DIR.glob("*.png"))
    report = WORK_DIR / "report.md"
    if charts:
        st.subheader("Charts")
        cols = st.columns(2)
        for i, chart in enumerate(charts):
            cols[i % 2].image(str(chart), caption=chart.name, use_container_width=True)
    if report.exists():
        st.subheader("Final report")
        text = report.read_text()
        st.markdown(text)
        st.download_button("Download report.md", text, file_name="report.md")


if question and uploaded is not None:
    with st.chat_message("user", avatar=AGENT_AVATARS["user"]):
        st.markdown(question)
    with st.spinner("Agents are analyzing your data…"):
        try:
            asyncio.run(run_and_render(uploaded.getvalue(), question))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
    show_outputs()
