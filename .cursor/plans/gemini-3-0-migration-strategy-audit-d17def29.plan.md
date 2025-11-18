<!-- d17def29-9163-4cae-9113-615a02a085d7 99b1a6f1-e859-41ba-ada5-f746f1fcddee -->
# Design Review Memo: Gemini 3.0 Pro Migration

## 1. Validation Findings

### Proposal 1: API Injection in `llm.py`

-   **Status:** **Valid but requires implementation change.**
-   **Findings:** `get_response_from_llm` in `ai_scientist/llm.py` uses the `openai` client library (v1.0+ assumed from usage). The client's `chat.completions.create` method **does** support `extra_body`.
-   **Correction:** The wrapper function `get_response_from_llm` does **not** currently accept `extra_body` or `**kwargs`. You cannot simply "pass it" to the function without modifying the function signature or its internal logic.
-   **Action:** We will modify `get_response_from_llm` (and `get_batch_responses_from_llm`) to internally inject `extra_body={"thinking_config": ...}` specifically when `model == "gemini-3.0-pro-preview"`.

### Proposal 2: Parsing Safety Net

-   **Status:** **Validated & Safe.**
-   **Findings:** `extract_json_between_markers` exists in `ai_scientist/llm.py` and is public.
-   **Dependency:** `ai_scientist/perform_ideation_temp_free.py` already imports from `ai_scientist.llm`. There is **no circular dependency risk** because `llm.py` does not import `perform_ideation_temp_free`.
-   **Action:** Proceed with replacing `json.loads` with `extract_json_between_markers`.

### Proposal 3: Concurrency Tuning

-   **Status:** **Valid but "Cleaner Way" available.**
-   **Findings:** `ai_scientist/treesearch/log_summarization.py` uses `ThreadPoolExecutor` with default workers.
-   **Cleaner Way:** `ai_scientist/treesearch/utils/config.py` defines `AgentConfig` with `num_workers`. The `overall_summarize` function accepts a `cfg` object. We should use `cfg.agent.num_workers` if available, with a fallback to `5`.

## 2. Logic Risks & Edge Cases

1.  **VLM Usage:** `ai_scientist/vlm.py` also calls Gemini (lines 109-119). The current plan only targets `llm.py`.

    -   *Recommendation:* We will apply the `thinking_config` **only to `llm.py`** for now, as image captioning/VLM tasks usually do not support/require "thinking" budgets.

2.  **Standalone Execution of Summarization:** The `__main__` block in `log_summarization.py` calls `overall_summarize` without a `cfg` object.

    -   *Fix:* The fallback logic `workers = cfg.agent.num_workers if cfg else 5` is critical to prevent crashes when running this script directly.

## 3. Refined Implementation Plan

### Step 1: `ai_scientist/llm.py`

-   Define `GEMINI_THINKING_CONFIG = {"thinking_budget": 16000, "include_thoughts": False}` constant.
-   Update `get_response_from_llm` and `get_batch_responses_from_llm`:
    -   Check if `model == "gemini-3.0-pro-preview"`.
    -   If yes, add `extra_body={"thinking_config": GEMINI_THINKING_CONFIG}` to the `client.chat.completions.create` call.

### Step 2: `ai_scientist/perform_ideation_temp_free.py`

-   Replace manual `re` search and `json.loads` blocks with calls to `extract_json_between_markers`.

### Step 3: `ai_scientist/treesearch/log_summarization.py`

-   Modify `overall_summarize` to determine `max_workers`:
    ```python
    max_workers = 5
    if cfg and hasattr(cfg, "agent") and hasattr(cfg.agent, "num_workers"):
        max_workers = cfg.agent.num_workers
    ```

-   Pass `max_workers=max_workers` to `ThreadPoolExecutor`.

This plan is robust and ready for execution.

### To-dos

- [ ] Modify ai_scientist/llm.py to inject Gemini thinking_config
- [ ] Refactor JSON parsing in ai_scientist/perform_ideation_temp_free.py
- [ ] Update concurrency logic in ai_scientist/treesearch/log_summarization.py