# Cloud Code Execution Engine (Judge0) Technical Documentation

## Overview

The **Cloud Code Execution Engine** (`python_backend/app/execution/`) provides remote, sandboxed code execution using **Judge0 CE**. Submitted code is never executed locally using `exec`, `subprocess`, or local Docker containers.

The execution engine integrates cleanly into the post-submission processing pipeline:

```text
Monaco Editor Final Submission (Phase 7)
               │
               ▼
   SubmissionProcessingInterface
               │
               ▼
 Phase 8 Execution Engine (Judge0)
               │
               ▼
  Static Analysis Engine (Phase 5)
               │
               ▼
    Gemini AI Review (Phase 6)
               │
               ▼
  Authority Review Dashboard (Phase 4/5/6/7/8)
```

---

## Architecture & Provider Abstraction

- **`BaseExecutionProvider`**: Abstract interface defining `submit()`, `get_result()`, `execute()`, and `health_check()`.
- **`Judge0ExecutionProvider`**: Asynchronous HTTP implementation communicating with Judge0 CE via `httpx`.
- **`ExecutionProviderFactory`**: Factory returning `BaseExecutionProvider`. Enables future provider replacement (e.g. AWS Runner, GCP Sandbox) without modifying business logic.

---

## Configuration Variables

Configured via environment variables (`.env`):

| Variable | Default | Description |
|---|---|---|
| `JUDGE0_API_URL` | `https://judge0-ce.p.rapidapi.com` | Base URL for Judge0 API |
| `JUDGE0_API_KEY` | `""` | RapidAPI / Judge0 API Key |
| `JUDGE0_REQUEST_TIMEOUT` | `30.0` | HTTP request timeout in seconds |
| `JUDGE0_POLL_INTERVAL` | `1.0` | Polling interval for submission token |
| `JUDGE0_MAX_POLL_ATTEMPTS` | `30` | Maximum polling attempts |
| `MAX_SOURCE_CODE_SIZE` | `524288` (500KB) | Max allowed code size in bytes |
| `MAX_TEST_CASES_PER_SUBMISSION` | `50` | Maximum test cases evaluated per run |

> [!CAUTION]
> **Credential Security**: Credentials (`JUDGE0_API_KEY`, headers) are strictly sanitized and never logged or exposed in API responses.

---

## Centralized Language Mapping

Mapped in `app/execution/language/judge0_language_map.py`:

| Identifier | Judge0 ID | Language Version |
|---|---|---|
| `python` | 71 | Python 3.8.1 |
| `java` | 62 | Java OpenJDK 13.0.1 |
| `javascript` | 63 | Node.js 12.14.0 |
| `typescript` | 74 | TypeScript 3.7.4 |
| `c` | 50 | GCC 9.2.0 |
| `cpp` | 54 | GCC 9.2.0 |
| `csharp` | 51 | Mono 6.6.0.161 |
| `go` | 60 | Go 1.13.5 |
| `rust` | 73 | Rust 1.40.0 |
| `php` | 68 | PHP 7.4.1 |
| `kotlin` | 78 | Kotlin 1.3.70 |
| `swift` | 83 | Swift 5.2.3 |

---

## API Reference

Mounted under `/api/v1/execution`:

### 1. `GET /api/v1/execution/health`
Checks provider availability and configuration status.

### 2. `POST /api/v1/execution/submission/{submission_id}`
Manually triggers code execution for a finalized submission (Authority/System role required).

### 3. `GET /api/v1/execution/submission/{submission_id}`
Returns aggregated execution summary including pass percentage, runtime, memory, and individual test results.

### 4. `GET /api/v1/execution/submission/{submission_id}/results`
Returns list of test case results. Inputs/outputs of hidden test cases are automatically masked for intern users.

### 5. `GET /api/v1/execution/{execution_id}`
Returns detail for a single test case execution result.

---

## Security & RBAC Controls

1. **Sandboxing**: Code runs exclusively inside remote Judge0 containers.
2. **Hidden Test Masking**: Interns receive pass/fail status and execution metrics, but `stdin`, `expected_output`, `actual_output`, and `stderr` for private/hidden test cases are omitted unless requested by an `authority`.
3. **Idempotency**: Submissions in `PROCESSING` or `COMPLETED` states reject duplicate execution attempts.
