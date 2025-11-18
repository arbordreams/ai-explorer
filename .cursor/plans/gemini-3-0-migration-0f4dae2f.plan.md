<!-- 0f4dae2f-9753-49ff-bd1c-18133f716d3e 7e769fe5-035d-4343-8d3b-e93954c3b166 -->
# Master Migration Plan: AI Scientist v2 -> Gemini 3.0 Pro

## 1. Core LLM Wrapper (`ai_scientist/llm.py`)

- **Define Config**: Add `GEMINI_3_CONFIG` constant with `thinking_level="high"` and `include_thoughts=False` nested under `google`.
- **Refactor `get_batch_responses_from_llm`**:
    - Force `temperature=1.0` for `gemini-3.0-pro-preview`.
    - Inject `extra_body` with `GEMINI_3_CONFIG`.
- **Refactor `get_response_from_llm`**:
    - Force `temperature=1.0` for `gemini-3.0-pro-preview`.
    - Inject `extra_body` with `GEMINI_3_CONFIG`.

## 2. Vision Module (`ai_scientist/vlm.py`)

- **Define Config**: Add `GEMINI_VISION_CONFIG` with `media_resolution="media_resolution_medium"`.
- **Refactor `make_vlm_call`** and `get_batch_responses_from_vlm`:
    - Update model checks to handle `gemini-3.0-pro-preview`.
    - Force `temperature=1.0`.
    - Inject `extra_body` with `GEMINI_VISION_CONFIG` nested under `google`.

## 3. Backend & Tool Usage (`ai_scientist/treesearch/backend/backend_openai.py`)

- **Update `query` function**:
    - Detect `gemini-3.0-pro-preview`.
    - Force `temperature=1.0`.
    - Inject `extra_body` with `GEMINI_3_CONFIG` (thinking config).

## 4. Safety & JSON Parsing (`ai_scientist/perform_ideation_temp_free.py`)

- **Import**: Ensure `extract_json_between_markers` is imported.
- **Refactor JSON Parsing**:
    - Locate `json.loads` calls processing LLM responses (around lines 214, 228).
    - Replace or wrap with `extract_json_between_markers` to handle potential text leaks.

## 5. Concurrency Control (`ai_scientist/treesearch/log_summarization.py`)

- **Refactor Threading**:
    - Change `ThreadPoolExecutor()` to `ThreadPoolExecutor(max_workers=5)` to respect the 50 RPM quota.

## 6. Verification

- Review changes to ensure all Gemini 3.0 specs are met.

### To-dos

- [ ] Update ai_scientist/llm.py with new config and injection logic
- [ ] Update ai_scientist/vlm.py with vision config and injection logic
- [ ] Update ai_scientist/treesearch/backend/backend_openai.py for backend tool calls
- [ ] Refactor JSON parsing in ai_scientist/perform_ideation_temp_free.py
- [ ] Limit concurrency in ai_scientist/treesearch/log_summarization.py