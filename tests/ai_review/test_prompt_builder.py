from ai_review.services.prompt_builder import ReviewPromptContext, PromptBuilder, PROMPT_TEMPLATES

def test_prompt_builder_v1():
    context = ReviewPromptContext(
        source_code="def is_even(n): return n % 2 == 0",
        programming_language="python",
        submission_id=101,
        assignment_description="Check if number is even",
        prompt_version="v1"
    )
    prompt = PromptBuilder.build_prompt(context)
    assert "def is_even(n):" in prompt
    assert "python" in prompt
    assert "Correctness (30%)" in prompt
    assert "REQUIRED OUTPUT FORMAT" in prompt

def test_prompt_builder_version_fallback():
    context = ReviewPromptContext(
        source_code="print('hello')",
        programming_language="python",
        submission_id=102,
        prompt_version="invalid_ver"
    )
    prompt = PromptBuilder.build_prompt(context)
    assert "def is_even" not in prompt  # Correct formatting for context
    assert "python" in prompt
