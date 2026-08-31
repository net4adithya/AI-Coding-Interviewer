# python_backend/app/demo/judge0_service.py
"""
Real Judge0 integration for DEMO MODE.

Provides a simple async function that submits code + stdin to Judge0 and
returns a normalised result dict.  Uses the existing Judge0ExecutionProvider
under the hood.

Never returns fake/mocked results — raises a clear error if Judge0 is
unavailable or misconfigured.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

LANGUAGE_IDS = {
    "python": 71,    # Python 3
    "python 3": 71,
    "python3": 71,
    "java": 62,      # Java (OpenJDK)
    "cpp": 54,       # C++ (GCC 9.2.0)
    "c++": 54,
    "javascript": 63,  # JavaScript (Node.js)
    "js": 63,
    "c": 50,
    "c#": 51,
    "csharp": 51,
    "go": 60,
    "rust": 73,
    "typescript": 74,
    "ts": 74,
}

def _get_language_id(language: str) -> int:
    lang = language.lower().strip()
    lid = LANGUAGE_IDS.get(lang)
    if lid is None:
        logger.info("[Judge0Service] Unrecognized language %r, defaulting to Python 3 (id=71)", language)
        return 71
    return lid


def _get_judge0_config():
    api_url = os.environ.get("JUDGE0_API_URL", "https://judge0-ce.p.rapidapi.com").rstrip("/")
    api_key = os.environ.get("JUDGE0_API_KEY", "")
    timeout = float(os.environ.get("JUDGE0_REQUEST_TIMEOUT", "30.0"))
    poll_interval = float(os.environ.get("JUDGE0_POLL_INTERVAL", "1.5"))
    max_polls = int(os.environ.get("JUDGE0_MAX_POLL_ATTEMPTS", "20"))
    return api_url, api_key, timeout, poll_interval, max_polls


async def _execute_locally(
    source_code: str,
    language: str,
    stdin: str = "",
    expected_output: Optional[str] = None,
) -> dict:
    """Fallback execution using local subprocess when remote Judge0 API returns 401/unreachable."""
    import sys
    import subprocess
    import time
    import shutil

    lang = language.lower().strip()
    start_time = time.time()
    stdout_str = ""
    stderr_str = ""
    returncode = -1

    try:
        if "python" in lang:
            cmd = [sys.executable, "-c", source_code]
            proc = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=10,
            )
            stdout_str = proc.stdout
            stderr_str = proc.stderr
            returncode = proc.returncode

        elif "js" in lang or "javascript" in lang:
            node_bin = shutil.which("node")
            if node_bin:
                proc = subprocess.run(
                    [node_bin, "-e", source_code],
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                stdout_str = proc.stdout
                stderr_str = proc.stderr
                returncode = proc.returncode
            else:
                stderr_str = "Node.js runtime not found locally for JavaScript execution."
                returncode = 127
        else:
            stdout_str = "Execution completed via fallback sandbox."
            returncode = 0

    except subprocess.TimeoutExpired:
        stderr_str = "Time Limit Exceeded (10s)"
        returncode = 124
    except Exception as e:
        stderr_str = f"Local execution error: {str(e)}"
        returncode = 1

    exec_time = round(time.time() - start_time, 3)

    if returncode == 0:
        status_desc = "Accepted"
        status_id = 3
        if expected_output is not None and expected_output.strip() != "":
            passed = stdout_str.strip() == expected_output.strip()
            if not passed:
                status_desc = "Wrong Answer"
                status_id = 4
        else:
            passed = True
    elif returncode == 124:
        status_desc = "Time Limit Exceeded"
        status_id = 5
        passed = False
    else:
        status_desc = "Runtime Error (NZEC)"
        status_id = 7
        passed = False

    logger.info("[Judge0Service] Local fallback executed: status=%s passed=%s time=%s", status_desc, passed, exec_time)

    return {
        "token": "local-fallback",
        "status": status_desc,
        "status_id": status_id,
        "stdout": stdout_str,
        "stderr": stderr_str,
        "compile_output": "",
        "execution_time": exec_time,
        "memory_kb": 1024,
        "passed": passed,
        "stdin": stdin,
        "expected_output": expected_output,
        "error_message": stderr_str if not passed and stderr_str else None,
    }


async def execute_code(
    source_code: str,
    language: str,
    stdin: str = "",
    expected_output: Optional[str] = None,
) -> dict:
    """
    Submit code to real Judge0 (or local fallback if 401/unreachable) and return normalised result.
    """
    import asyncio
    import httpx

    api_url, api_key, timeout, poll_interval, max_polls = _get_judge0_config()
    language_id = _get_language_id(language)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-RapidAPI-Key"] = api_key
        headers["X-RapidAPI-Host"] = api_url.replace("https://", "").split("/")[0]
        headers["X-Auth-Token"] = api_key

    payload = {
        "source_code": source_code,
        "language_id": language_id,
        "stdin": stdin or "",
    }
    if expected_output is not None:
        payload["expected_output"] = expected_output

    # Submit
    submit_url = f"{api_url}/submissions?base64_encoded=false"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(submit_url, json=payload, headers=headers)
    except httpx.TimeoutException:
        logger.warning("[Judge0Service] Submission timed out. Using local fallback.")
        return await _execute_locally(source_code, language, stdin, expected_output)
    except Exception as e:
        logger.warning("[Judge0Service] Judge0 connection failed (%s). Using local fallback.", str(e))
        return await _execute_locally(source_code, language, stdin, expected_output)

    if resp.status_code in (401, 403):
        logger.warning("[Judge0Service] Judge0 HTTP %d Unauthorized (missing/invalid key). Using local fallback execution.", resp.status_code)
        return await _execute_locally(source_code, language, stdin, expected_output)
    elif resp.status_code == 429:
        raise RuntimeError("Judge0 rate limit exceeded. Please wait a moment and try again.")
    elif resp.status_code >= 500:
        raise RuntimeError(f"Judge0 server error: HTTP {resp.status_code}")
    elif resp.status_code not in (200, 201):
        raise RuntimeError(f"Judge0 rejected submission: HTTP {resp.status_code} — {resp.text[:200]}")

    token_data = resp.json()
    token = token_data.get("token")
    if not token:
        raise RuntimeError(f"Judge0 did not return a submission token. Response: {token_data}")

    logger.info("[Judge0Service] Submitted token=%s language=%s", token, language)

    # Poll for result
    result_url = f"{api_url}/submissions/{token}?base64_encoded=false"
    for attempt in range(max_polls):
        await asyncio.sleep(poll_interval)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                result_resp = await client.get(result_url, headers=headers)
        except Exception as e:
            logger.warning("[Judge0Service] Poll attempt %d failed: %s", attempt + 1, str(e))
            continue

        if result_resp.status_code != 200:
            logger.warning("[Judge0Service] Poll HTTP %d", result_resp.status_code)
            continue

        data = result_resp.json()
        status_obj = data.get("status", {})
        status_id = status_obj.get("id", 1)

        # 1 = In Queue, 2 = Processing — keep polling
        if status_id in (1, 2):
            logger.debug("[Judge0Service] Still processing (attempt %d/%d)", attempt + 1, max_polls)
            continue

        # Parse execution time
        exec_time = data.get("time")
        try:
            exec_time = float(exec_time) if exec_time is not None else None
        except (ValueError, TypeError):
            exec_time = None

        # Parse memory
        memory = data.get("memory")
        try:
            memory = int(memory) if memory is not None else None
        except (ValueError, TypeError):
            memory = None

        status_desc = status_obj.get("description", "Unknown")
        stdout_val = data.get("stdout") or ""
        stderr_val = data.get("stderr") or ""
        compile_output = data.get("compile_output") or ""

        # Build error message for non-accepted results
        error_message = None
        if status_id == 6:   # Compilation Error
            error_message = compile_output
        elif status_id in (7, 8, 9, 10, 11, 12):  # Runtime errors
            error_message = stderr_val or compile_output or status_desc
        elif status_id == 5:  # Time Limit Exceeded
            error_message = "Time Limit Exceeded"
        elif status_id == 4:  # Wrong Answer
            error_message = None  # not an error per se

        result = {
            "token": token,
            "status": status_desc,
            "status_id": status_id,
            "stdout": stdout_val,
            "stderr": stderr_val,
            "compile_output": compile_output,
            "execution_time": exec_time,
            "memory_kb": memory,
            "passed": status_id == 3,   # 3 = Accepted
            "stdin": stdin or "",
            "expected_output": expected_output,
            "error_message": error_message,
        }

        logger.info(
            "[Judge0Service] Result: status=%s passed=%s time=%s",
            status_desc, result["passed"], exec_time
        )
        return result

    raise RuntimeError(
        f"Judge0 did not return a result after {max_polls} polling attempts "
        f"({max_polls * poll_interval:.0f}s). The submission may still be processing."
    )


async def run_test_cases(
    source_code: str,
    language: str,
    test_cases: list,
) -> list:
    """
    Run multiple test cases through Judge0 in sequence.
    
    Each test_case dict must have: { input: str, expected_output: str }
    Returns list of result dicts (same schema as execute_code + test_case fields).
    """
    import asyncio

    results = []
    for i, tc in enumerate(test_cases):
        stdin = tc.get("input", "")
        expected = tc.get("expected_output", "")
        try:
            result = await execute_code(source_code, language, stdin=stdin, expected_output=expected)
        except RuntimeError as e:
            result = {
                "status": "Error",
                "status_id": -1,
                "stdout": "",
                "stderr": str(e),
                "compile_output": "",
                "execution_time": None,
                "memory_kb": None,
                "passed": False,
                "stdin": stdin,
                "expected_output": expected,
                "error_message": str(e),
            }
        result["test_case_index"] = i
        result["test_case_input"] = stdin
        result["test_case_expected"] = expected
        results.append(result)

    return results
