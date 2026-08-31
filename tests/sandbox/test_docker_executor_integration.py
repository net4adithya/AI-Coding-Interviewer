"""Integration tests for Docker sandbox executor (requires Docker daemon)."""

import shutil

import pytest

from app.sandbox.executor import DockerSandboxExecutor
from app.sandbox.schemas import ExecutionStatus


def _docker_daemon_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        import docker
        docker.from_env().ping()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _docker_daemon_available(), reason="Docker daemon not available")


@pytest.fixture(scope="module")
def executor():
    try:
        return DockerSandboxExecutor()
    except DockerNotAvailableError:
        pytest.skip("Docker daemon not running")


def test_python_stdin_multiply(executor):
    result = executor.execute(
        language="python",
        source_code="print(int(input()) * 2)",
        stdin="5",
    )
    assert result.status == ExecutionStatus.ACCEPTED
    assert result.stdout.strip() == "10"


def test_python_runtime_error(executor):
    result = executor.execute(
        language="python",
        source_code='raise Exception("test")',
        stdin="",
    )
    assert result.status == ExecutionStatus.RUNTIME_ERROR


def test_python_timeout(executor, monkeypatch):
    monkeypatch.setattr("app.sandbox.config.sandbox_settings.EXECUTION_TIMEOUT_SEC", 2.0)
    result = executor.execute(
        language="python",
        source_code="while True:\n    pass",
        stdin="",
    )
    assert result.status == ExecutionStatus.TIME_LIMIT_EXCEEDED


def test_javascript_stdout(executor):
    result = executor.execute(
        language="javascript",
        source_code="console.log(2 + 3)",
        stdin="",
    )
    assert result.status == ExecutionStatus.ACCEPTED
    assert result.stdout.strip() == "5"


def test_cpp_stdout(executor):
    result = executor.execute(
        language="cpp",
        source_code=(
            "#include <iostream>\n"
            "using namespace std;\n"
            "int main() { cout << 7; return 0; }\n"
        ),
        stdin="",
    )
    assert result.status == ExecutionStatus.ACCEPTED
    assert result.stdout.strip() == "7"


def test_java_stdout(executor):
    result = executor.execute(
        language="java",
        source_code=(
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(9);\n"
            "    }\n"
        ),
        stdin="",
    )
    assert result.status == ExecutionStatus.ACCEPTED
    assert result.stdout.strip() == "9"
