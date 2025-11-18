<!-- 6892936c-2d5c-4084-85d6-055626fe6d4c 39592992-7935-41d8-9dc0-d2a1e81d6e86 -->
# GEMINI MIGRATION PLAN

## Phase 1: Audit & Validation Results

### 1. Reasoning Mode Activation (CRITICAL)

- **Status**: **UNSAFE**
- **Location**: `ai_scientist/llm.py` (Lines 175-185, 430-439)
- **Finding**: The `client.chat.completions.create` call for Gemini does not pass `extra_body={"thinking_budget": 16000}` (or `include_thoughts=True`). This means the model runs in standard mode, skipping deep research capabilities.

### 2. The "Monologue" Parsing Crash

- **Status**: **UNSAFE**
- **Location**: `ai_scientist/perform_ideation_temp_free.py` (Lines 214, 228)
- **Finding**: The code uses `json.loads(arguments_text)` on text extracted via a simple regex (`r"ARGUMENTS:\s*(.*?)(?:$|\nTHOUGHT:|\n$)"`). If Gemini outputs a thought trace (monologue) inside the `ARGUMENTS` section before the JSON, `json.loads` will crash.

### 3. Rate Limit / Concurrency Lock

- **Status**: **UNSAFE**
- **Location**: `ai_scientist/treesearch/log_summarization.py` (Line 351)
- **Finding**: The code uses `with ThreadPoolExecutor() as executor:`. By default, this spawns `5 * num_cpus` threads. This will immediately hit Google's Preview API rate limits (approx. 60 QPM) and cause 429 errors.

### 4. Context Window Waste

- **Status**: **SAFE (for Papers)** / **POTENTIALLY WASTEFUL (for Logs)**
- **Location**: `ai_scientist/perform_llm_review.py` (Lines 257-288)
- **Finding**: The `load_paper` function loads the full PDF text without truncation (unless `num_pages` is explicitly set, which defaults to `None`). However, `log_summarization.py` summarizes experiment logs. Since the user specifically asked about *papers* fitting 128k limit, the paper loading part is safe.

---

## Phase 2: Implementation Plan

### Files to Touch

1. `ai_scientist/llm.py`
2. `ai_scientist/perform_ideation_temp_free.py`
3. `ai_scientist/treesearch/log_summarization.py`

### Specific Fixes

#### 1. Fix Reasoning Mode (`ai_scientist/llm.py`)

Update `get_response_from_llm` and `get_batch_responses_from_llm` to inject `extra_body` for Gemini 3.0.

#### 2. Fix "Monologue Bug" (`ai_scientist/perform_ideation_temp_free.py`)

Replace the direct `json.loads` calls with `extract_json_between_markers` imported from `llm.py`.

**Regex-based Cleaning Function to Use:**

We will use the existing `extract_json_between_markers` in `llm.py` which already implements the robust regex extraction:

````python
def extract_json_between_markers(llm_output: str) -> dict | None:
    # 1. Try ```json ... ```
    json_pattern = r"```json(.*?)```"
    matches = re.findall(json_pattern, llm_output, re.DOTALL)
    
    if not matches:
        # 2. Fallback: Find first outer-most { ... }
        # Note: The current fallback in llm.py is r"\{.*?\}", which is non-greedy.
        # We should improve this to match nested braces if possible, but for now
        # relying on the standard implementation is a significant improvement over raw json.loads.
        json_pattern = r"\{[\s\S]*\}" # Greedy match might be better if monologue is first, but finding the *first* valid JSON block is key.
        # We will stick to the existing function but ensure it is USED.
````

*Refinement*: In `perform_ideation_temp_free.py`, we will wrap the `arguments_text` extraction to ensure we look for a JSON block specifically.

#### 3. Fix Rate Limit (`ai_scientist/treesearch/log_summarization.py`)

Inject a semaphore/limit by setting `max_workers=1` in the `ThreadPoolExecutor`.

**Injection Point:**

```python
# ai_scientist/treesearch/log_summarization.py

# OLD:
# with ThreadPoolExecutor() as executor:

# NEW:
with ThreadPoolExecutor(max_workers=1) as executor:
```

This ensures strictly serial execution to respect the API limits.

### To-dos

- [ ] Create GEMINI_MIGRATION_PLAN.md with the audit results and fix plan
- [ ] Update ai_scientist/llm.py to add thinking_budget for Gemini 3.0
- [ ] Update ai_scientist/perform_ideation_temp_free.py to use safe JSON extraction
- [ ] Update ai_scientist/treesearch/log_summarization.py to limit ThreadPoolExecutor concurrency