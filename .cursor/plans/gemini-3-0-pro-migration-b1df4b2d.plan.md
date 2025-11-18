<!-- b1df4b2d-ceae-4af7-8c87-a238941b4969 c834e76f-60e0-4a13-be9d-fcca60167b2f -->
# Gemini 3.0 Pro Migration Plan

## 1. Update Master Configuration in `ai_scientist/llm.py`

- Update `GEMINI_THINKING_CONFIG` constant with the new specification:
- `thinking_level`: "high"
- `include_thoughts`: False
- `media_resolution`: "media_resolution_medium"
- Update `get_batch_responses_from_llm` and `get_response_from_llm` to inject this config into `extra_body` for `gemini-3.0-pro-preview`.
- Ensure `temperature` is forced to `1.0` for this model.

## 2. Fix JSON Parsing in `ai_scientist/perform_ideation_temp_free.py`

- Import `extract_json_between_markers` from `ai_scientist.llm`.
- Replace strict `json.loads` with `extract_json_between_markers` to handle potential Markdown leakage or preambles in the arguments.

## 3. Implement Rate Limiting in `ai_scientist/treesearch/log_summarization.py`

- Restrict `ThreadPoolExecutor` to `max_workers=5` to avoid hitting Google's burst limits (429 errors).

### To-dos

- [ ] Update GEMINI_THINKING_CONFIG and injection logic in ai_scientist/llm.py
- [ ] Fix JSON parsing in ai_scientist/perform_ideation_temp_free.py
- [ ] Restrict ThreadPoolExecutor in ai_scientist/treesearch/log_summarization.py