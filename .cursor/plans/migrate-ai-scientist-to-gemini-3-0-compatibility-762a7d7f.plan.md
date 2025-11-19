<!-- 762a7d7f-f2dc-4aea-9321-ad4db6f75087 d30a5582-86f7-494d-83db-3be00143e565 -->
# Migrate AI Scientist to Gemini 3.0 Compatibility

This plan outlines the steps to update the AI Scientist codebase for full compatibility with the Gemini 3.0 model family, adhering to Google's official migration guidelines.

## 1. Update Model Configurations

- **Reasoning:** Gemini 3.0 uses `thinking_level` instead of `thinking_budget` or `reasoning_effort` (OpenAI compatibility mapping). We need to ensure the configuration correctly sets this.
- **Files:** `ai_scientist/treesearch/backend/backend_openai.py`, `ai_scientist/vlm.py`
- **Actions:**
    - Remove `GEMINI_3_CONFIG` dictionary and injection logic in `backend_openai.py`. Keep `temperature=1.0`.
    - Remove `GEMINI_VISION_CONFIG` dictionary and injection logic in `vlm.py`. Keep `temperature=1.0`.
    - We will rely on defaults for thinking_level (High) and media_resolution (Optimal) as passing them via `extra_body` is causing errors with the OpenAI client wrapper.

## 2. Fix API Parameter Injection

- **Reasoning:** The error `Invalid JSON payload received. Unknown name "google": Cannot find field.` indicates that passing `extra_body={"google": ...}` through the OpenAI client wrapper is failing for some endpoints or configurations.
- **Files:** `ai_scientist/vlm.py`, `ai_scientist/treesearch/backend/backend_openai.py`
- **Actions:**
    - Modify `ai_scientist/vlm.py` to **remove** the injection of `extra_body=GEMINI_VISION_CONFIG` for `gemini-3.0-pro-preview` calls.
    - Modify `ai_scientist/treesearch/backend/backend_openai.py` to **remove** the injection of `extra_body=GEMINI_3_CONFIG`.
    - Refactor `make_vlm_call` and `make_llm_call` to use standard OpenAI parameters where possible (e.g., `reasoning_effort='medium'` for high thinking) instead of the custom `google` dictionary if the endpoint rejects it.

## 3. Prompt Engineering Updates

- **Reasoning:** Gemini 3.0 prefers concise instructions and may over-analyze verbose CoT prompts.
- **Files:** `ai_scientist/treesearch/parallel_agent.py`, `ai_scientist/treesearch/agent_manager.py`
- **Actions:**
    - Review system prompts. Remove explicit "Let's think step by step" instructions if `thinking_level` is enabled, as the model does this natively.
    - Ensure instructions are placed *after* large context blocks (like codebases or datasets).

## 4. Verification

- **Reasoning:** We need to ensure the changes actually work and the API calls succeed.
- **Actions:**
    - Run `test_vlm_standalone.py` to verify VLM calls work without 400 errors.
    - Run `smoke_test.yaml` to verify the full agent loop (LLM + VLM) works.

## Implementation Plan

1.  **Fix VLM API Call (Priority):**

    - Edit `ai_scientist/vlm.py`: Remove `GEMINI_VISION_CONFIG` definition and `extra_body` injection logic in `make_vlm_call` and `get_batch_responses_from_vlm`.

2.  **Fix Backend LLM Call:**

    - Edit `ai_scientist/treesearch/backend/backend_openai.py`: Remove `GEMINI_3_CONFIG` definition and `extra_body` injection logic in `query`.

3.  **Verify VLM:**

    - Run `python test_vlm_standalone.py`.

4.  **Verify Full Agent:**

    - Run `python launch_scientist_bfts.py --config smoke_test.yaml --task_file task_description.txt`.

### To-dos

- [ ] Verify VLM with test_vlm_standalone.py
- [ ] Verify Full Agent with smoke_test.yaml