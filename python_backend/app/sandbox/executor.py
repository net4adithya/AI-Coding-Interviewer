"""Docker-based isolated code execution."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from typing import Optional

from app.sandbox.config import sandbox_settings
from app.sandbox.language_config import is_compilation_exit_code, resolve_language
from app.sandbox.schemas import ExecutionResponse, ExecutionStatus

logger = logging.getLogger(__name__)


class DockerNotAvailableError(RuntimeError):
    pass


class UnsupportedLanguageError(ValueError):
    pass


def _truncate(text: str, limit: int) -> str:
    if len(text.encode("utf-8")) <= limit:
        return text
    encoded = text.encode("utf-8")[:limit]
    return encoded.decode("utf-8", errors="ignore") + "\n...[output truncated]"


def _get_docker_client():
    try:
        import docker
    except ImportError as exc:
        raise DockerNotAvailableError(
            "docker package is not installed. Run: pip install docker"
        ) from exc
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as exc:
        raise DockerNotAvailableError(f"Docker daemon unavailable: {exc}") from exc


class DockerSandboxExecutor:
    """Runs candidate code inside a restricted Docker container."""

    def execute(
        self,
        language: str,
        source_code: str,
        stdin: str = "",
        question_id: Optional[str] = None,
    ) -> ExecutionResponse:
        lang = resolve_language(language)
        if not lang:
            raise UnsupportedLanguageError(f"Unsupported language: {language!r}")

        if len(source_code.encode("utf-8")) > sandbox_settings.MAX_SOURCE_CODE_BYTES:
            return ExecutionResponse(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr="Source code exceeds maximum allowed size.",
                exit_code=-1,
            )

        if len(stdin.encode("utf-8")) > sandbox_settings.MAX_STDIN_BYTES:
            return ExecutionResponse(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr="Stdin exceeds maximum allowed size.",
                exit_code=-1,
            )

        work_dir = tempfile.mkdtemp(prefix="sandbox_exec_")
        container = None
        start = time.perf_counter()

        try:
            src_path = os.path.join(work_dir, lang.source_filename)
            with open(src_path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(source_code)

            if stdin:
                with open(os.path.join(work_dir, "input.txt"), "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(stdin)

            os.chmod(work_dir, 0o777)

            client = _get_docker_client()
            mem_limit = f"{sandbox_settings.EXECUTION_MEMORY_MB}m"
            nano_cpus = int(sandbox_settings.EXECUTION_CPUS * 1_000_000_000)

            container = client.containers.run(
                image=lang.docker_image,
                command=["/bin/sh", "-c", lang.run_script],
                volumes={os.path.abspath(work_dir): {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                network_mode="none",
                mem_limit=mem_limit,
                nano_cpus=nano_cpus,
                pids_limit=128,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=False,
                detach=True,
                stdout=True,
                stderr=True,
                user="nobody",
            )

            timeout = sandbox_settings.EXECUTION_TIMEOUT_SEC
            try:
                wait_result = container.wait(timeout=timeout)
                exit_code = int(wait_result.get("StatusCode", 1))
                timed_out = False
            except Exception:
                timed_out = True
                try:
                    container.kill()
                except Exception:
                    pass
                exit_code = 124

            stdout = _truncate(container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace"), sandbox_settings.MAX_OUTPUT_BYTES)
            stderr = _truncate(container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace"), sandbox_settings.MAX_OUTPUT_BYTES)

            elapsed_ms = int((time.perf_counter() - start) * 1000)

            if timed_out:
                status = ExecutionStatus.TIME_LIMIT_EXCEEDED
            elif is_compilation_exit_code(exit_code):
                status = ExecutionStatus.COMPILATION_ERROR
            elif exit_code == 0:
                status = ExecutionStatus.ACCEPTED
            else:
                status = ExecutionStatus.RUNTIME_ERROR

            return ExecutionResponse(
                status=status,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time_ms=elapsed_ms,
                memory_kb=0,
            )

        except UnsupportedLanguageError:
            raise
        except DockerNotAvailableError as exc:
            logger.error("[Sandbox] Docker unavailable: %s", exc)
            return ExecutionResponse(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr=str(exc),
                exit_code=-1,
                execution_time_ms=int((time.perf_counter() - start) * 1000),
            )
        except Exception as exc:
            logger.exception("[Sandbox] Execution failed for question=%s lang=%s", question_id, language)
            return ExecutionResponse(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr=str(exc),
                exit_code=-1,
                execution_time_ms=int((time.perf_counter() - start) * 1000),
            )
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            shutil.rmtree(work_dir, ignore_errors=True)
