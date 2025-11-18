<!-- e8b2f67e-e61e-45b3-a99e-91723aa60e9c 7493e604-a1ed-4fbf-8d80-3490cc529054 -->
# Update All Models to Gemini 3.0 Pro Preview

This plan will update all default model configurations and arguments across the codebase to use `gemini-3.0-pro-preview` as requested, ensuring consistent usage of the new model while preserving existing functionality for other models.

## 1. Update Config (`bfts_config.yaml`)

- Update `report` model to `gemini-3.0-pro-preview` (temp 1.0).
- Update commented-out defaults for `summary` and `select_node` to `gemini-3.0-pro-preview` for consistency.

## 2. Update Launch Script (`launch_scientist_bfts.py`)

- Change default values in `argparse` for:
    - `--model_agg_plots`
    - `--model_writeup`
    - `--model_citation`
    - `--model_writeup_small`
    - `--model_review`
All to `gemini-3.0-pro-preview`.

## 3. Update Writeup Scripts

- **`ai_scientist/perform_writeup.py`**:
    - Update default `small_model` and `big_model` arguments in `perform_writeup`.
- **`ai_scientist/perform_icbinb_writeup.py`**:
    - Update default `small_model` in `gather_citations`.
    - Update default `small_model` and `big_model` in `perform_writeup`.

## 4. Update Tree Search Journal (`ai_scientist/treesearch/journal.py`)

- Update hardcoded fallback "gpt-4o" strings to "gemini-3.0-pro-preview" in `get_best_node` and other helper functions.

## 5. Verification

- Verify all updates are syntactically correct.
- Ensure temperature settings are respected (implied by previous `llm.py` changes that enforce temp=1.0 for this model ID).

### To-dos

- [ ] Update bfts_config.yaml report model
- [ ] Update launch_scientist_bfts.py argparse defaults
- [ ] Update perform_writeup.py defaults
- [ ] Update perform_icbinb_writeup.py defaults
- [ ] Update journal.py defaults