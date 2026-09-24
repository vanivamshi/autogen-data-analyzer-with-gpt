"""Docker sandbox that runs all agent-generated Python code."""
import docker
from docker.errors import ImageNotFound
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

from config.settings import CODE_TIMEOUT, DOCKER_IMAGE, DOCKERFILE_DIR, WORK_DIR


def ensure_image() -> None:
    """Build the sandbox image from docker/Dockerfile the first time it is needed."""
    client = docker.from_env()
    try:
        client.images.get(DOCKER_IMAGE)
    except ImageNotFound:
        client.images.build(path=str(DOCKERFILE_DIR), tag=DOCKER_IMAGE, rm=True)


def get_docker_executor() -> DockerCommandLineCodeExecutor:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ensure_image()
    return DockerCommandLineCodeExecutor(
        image=DOCKER_IMAGE,
        work_dir=WORK_DIR,
        timeout=CODE_TIMEOUT,
        delete_tmp_files=True,
    )
