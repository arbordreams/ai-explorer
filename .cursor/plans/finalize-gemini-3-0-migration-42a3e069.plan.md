<!-- 42a3e069-4648-48d3-8f68-3374c928f357 dacf050b-aac3-422a-8617-c51f9063748b -->
# Finalize Gemini 3.0 Migration

This plan implements the user's specific migration instructions, updated to align with the Gemini 3.0 documentation (using `thinking_level` instead of `thinking_budget`).

## Task 1: Robustify `ai_scientist/llm.py`

- **Goal**: Inject the correct Gemini 3.0 reasoning configuration.
- **Changes**:
  - Define `GEMINI_THINKING_CONFIG` constant at the top of `llm.py`:
    ```python
    GEMINI_THINKING_CONFIG = {
        "google": {
            "thinking_config": {
                "thinking_level": "high",
                "include_thoughts": False
            }
        }
    }
    ```

  - Update `get_batch_responses_from_llm` and `get_response_from_llm` to:
    - Remove any legacy `thinking_budget` logic.
    - Check if `model == "gemini-3.0-pro-preview"`.
    - Inject `extra_body=GEMINI_THINKING_CONFIG` into the `client.chat.completions.create` kwargs.

## Task 2: Fix Parsing in `ai_scientist/perform_ideation_temp_free.py`

- **Goal**: Use robust JSON extraction to handle potential monologue leakage.
- **Changes**:
  - Import `extract_json_between_markers` from `ai_scientist.llm`.
  - Replace the fragile `json.loads(arguments_text)` with `extract_json_between_markers(arguments_text)`.

## Task 3: Tune Concurrency in `ai_scientist/treesearch/log_summarization.py`

- **Goal**: Respect the 50 RPM rate limit.
- **Changes**:
  - In `overall_summarize`, update the `ThreadPoolExecutor` initialization to `max_workers=5`.

## Verification

- Ensure no `thinking_budget` parameters remain in the Gemini config.
- Verify imports are correct.

### To-dos

- [ ] Modify `ai_scientist/llm.py` to include `GEMINI_THINKING_CONFIG` and inject it into `get_batch_responses_from_llm` and `get_response_from_llm`.
- [ ] Update `ai_scientist/perform_ideation_temp_free.py` to import and use `extract_json_between_markers`.
- [ ] Update `ai_scientist/treesearch/log_summarization.py` to limit `ThreadPoolExecutor` to 5 workers.