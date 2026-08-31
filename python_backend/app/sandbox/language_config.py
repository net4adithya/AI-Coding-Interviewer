"""Server-controlled language → Docker image and run scripts."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class LanguageConfig:
    language_id: str
    docker_image: str
    source_filename: str
    run_script: str


# Official slim images — server-controlled; candidate cannot override.
_LANGUAGE_MAP: Dict[str, LanguageConfig] = {
    "python": LanguageConfig(
        language_id="python",
        docker_image="python:3.12-slim",
        source_filename="main.py",
        run_script=(
            "if [ -f input.txt ]; then python -u main.py < input.txt; "
            "else python -u main.py; fi"
        ),
    ),
    "python3": LanguageConfig(
        language_id="python",
        docker_image="python:3.12-slim",
        source_filename="main.py",
        run_script=(
            "if [ -f input.txt ]; then python -u main.py < input.txt; "
            "else python -u main.py; fi"
        ),
    ),
    "javascript": LanguageConfig(
        language_id="javascript",
        docker_image="node:20-alpine",
        source_filename="main.js",
        run_script=(
            "if [ -f input.txt ]; then node main.js < input.txt; "
            "else node main.js; fi"
        ),
    ),
    "js": LanguageConfig(
        language_id="javascript",
        docker_image="node:20-alpine",
        source_filename="main.js",
        run_script=(
            "if [ -f input.txt ]; then node main.js < input.txt; "
            "else node main.js; fi"
        ),
    ),
    "cpp": LanguageConfig(
        language_id="cpp",
        docker_image="gcc:13",
        source_filename="main.cpp",
        run_script=(
            "if ! g++ -std=c++17 -O2 -o main main.cpp 2>compile.err; then "
            "cat compile.err >&2; exit 42; fi; "
            "if [ -f input.txt ]; then ./main < input.txt; else ./main; fi"
        ),
    ),
    "c++": LanguageConfig(
        language_id="cpp",
        docker_image="gcc:13",
        source_filename="main.cpp",
        run_script=(
            "if ! g++ -std=c++17 -O2 -o main main.cpp 2>compile.err; then "
            "cat compile.err >&2; exit 42; fi; "
            "if [ -f input.txt ]; then ./main < input.txt; else ./main; fi"
        ),
    ),
    "java": LanguageConfig(
        language_id="java",
        docker_image="eclipse-temurin:17-jdk",
        source_filename="Main.java",
        run_script=(
            "if ! javac Main.java 2>compile.err; then "
            "cat compile.err >&2; exit 42; fi; "
            "if [ -f input.txt ]; then java Main < input.txt; else java Main; fi"
        ),
    ),
}

_COMPILE_EXIT_CODE = 42


def resolve_language(language: str) -> Optional[LanguageConfig]:
    return _LANGUAGE_MAP.get(language.lower().strip())


def is_compilation_exit_code(code: int) -> bool:
    return code == _COMPILE_EXIT_CODE
