"""Central configuration, read from environment / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Temp storage shared between the host and the Docker sandbox (bind-mounted).
WORK_DIR = BASE_DIR / os.getenv("WORK_DIR", "temp")
DATA_FILENAME = "data.csv"

# Sandbox image: amancevice/pandas:2.2.2 plus matplotlib/seaborn (see docker/Dockerfile).
BASE_IMAGE = "amancevice/pandas:2.2.2"
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "autogen-data-analyzer:latest")
DOCKERFILE_DIR = BASE_DIR / "docker"
CODE_TIMEOUT = int(os.getenv("CODE_TIMEOUT", "120"))

TERMINATION_WORD = "TERMINATE"
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "80"))
MAX_TOOL_ITERATIONS = int(os.getenv("MAX_TOOL_ITERATIONS", "6"))
