# Align-and-Grow (A&G): Compute-Aware Vocabulary Transfer for Medical NLP

## 1. Background & Motivation
Adapting Large Language Models (LLMs) to specialized domains like medicine is hindered by **vocabulary mismatch**. General-purpose tokenizers fragment complex medical terms (e.g., "acetylcholinesterase" $\to$ "acetyl", "ch", "oline", "ster", "ase"), causing:
1.  **Compute Inefficiency**: Inflated sequence lengths increase training/inference cost linearly (or quadratically for attention).
2.  **Semantic Dilution**: The model struggles to compose the meaning of a complex concept from generic sub-words.

### The Gap in Existing Literature
*   **Static Alignment (e.g., TokAlign)**: Focuses on *initializing* embeddings for a fixed target vocabulary. It misses the opportunity to discover *new* terms dynamically during training.
*   **Naive Expansion (e.g., AdaptiVocab)**: Adds terms based purely on frequency. This often leads to "vocabulary bloat" (adding useless terms) and "initialization shock" (loss spikes due to random/poor initialization of new embeddings).

## 2. Novelty: The Align-and-Grow (A&G) Method
A&G unifies vocabulary expansion and alignment into a **compute-aware, adaptive loop**. Unlike one-shot methods, A&G co-evolves the tokenizer and model under a strict compute budget.

**Key Innovations:**
1.  **Gradient-Guided Discovery**: We score candidates not just by frequency, but by **learning difficulty** (gradient magnitude of current sub-tokens). If the model is struggling to predict "ch" + "oline", we merge them.
2.  **Local Re-alignment**: We only re-align the *newly added* tokens using a weighted average of their constituents (Soft-Mix), avoiding catastrophic forgetting of the base vocabulary.
3.  **Compute-Aware Gating**: A burst is only kept if it improves **Tokens-to-Target-Perplexity (TtTP)**, a novel metric that strictly enforces efficiency.

## 3. Implementation Plan

### 3.1. System & Hardware Setup
*   **Hardware**: Single **A100 40GB** (or RTX A6000 48GB).
*   **Base Model**: **Qwen/Qwen2.5-7B-Instruct** (Open weights, SOTA performance, no gating issues).
*   **Training Method**: **LoRA (Low-Rank Adaptation)**.
    *   *Rank*: $r=16$ or $32$.
    *   *Target Modules*: `q_proj`, `v_proj`, `k_proj`, `embed_tokens`, `lm_head`.
    *   *Note*: We MUST train `embed_tokens` and `lm_head` to learn the new vocabulary.
*   **Data**: A subset of PubMed/PMC (approx. 500MB - 1GB curated text).

### 3.2. Algorithm Steps

#### Phase 1: Seed Augmentation (S0)
*Goal: Fix the most obvious fragmentation immediately.*
1.  **Mining**: Scan corpus for top 2,000 terms with highest $\Delta \text{tokens} = \text{freq}(t) \times (\text{pieces}(t) - 1)$.
2.  **TokAlign Init**: Initialize new embeddings $E_{new}$ as the frequency-weighted average of their constituent sub-tokens $E_{sub}$ from the base model.
3.  **Seed Training**: Train for ~500 steps to stabilize.

#### Phase 2: Adaptive Growth Loop (The Core)
*Repeat for 4-5 cycles (Bursts) or until 8-hour timeout:*

1.  **Mine & Score**:
    Identify candidates $t$ from the last $N$ batches. Score using:
    $$ s(t) = \lambda_1 \underbrace{\Delta\text{tokens}(t)}_{\text{Efficiency}} + \lambda_2 \underbrace{\frac{1}{|P_t|} \sum_{p \in P_t} \| \nabla \mathcal{L}(p) \|_2}_{\text{Gradient Signal (Difficulty)}} $$
    *   Where $P_t$ are the sub-tokens currently representing term $t$.
    *   *Insight*: High gradients on sub-tokens imply the model is "working hard" to predict them; merging them relieves this stress.

2.  **Burst Selection**: Select top $b=100$ terms.

3.  **Local Re-alignment**:
    *   Resize tokenizer and embedding matrix.
    *   Initialize new rows using **Soft-Mix** (weighted avg of constituents).

4.  **Stabilization (The "Refit")**:
    *   **Freeze** the transformer backbone.
    *   **Train** only `embed_tokens` and `lm_head` (and LoRA adapters) with a higher LR ($2\text{e-}4$) for 200 steps.
    *   *Why?* Prevents the new random-ish embeddings from wrecking the pre-trained weights.

5.  **Guardrail Gate**:
    *   Measure **TtTP** on dev set: $\text{Total Tokens} \times \mathbb{I}(\text{PPL} < \tau)$.
    *   **Keep** if TtTP improves or PPL drops significantly.
    *   **Revert** if metrics degrade (load previous checkpoint).

### 3.3. Evaluation Metrics
*   **Primary (Efficiency)**: **TtTP (Tokens-to-Target-Perplexity)**. Lower is better.
*   **Secondary (Quality)**: Perplexity (PPL) on held-out medical text.
*   **Diagnostic**: Tokens per Document (Compression Ratio).

## 4. Resource Budget (8-Hour Limit)
*   **Setup & Data**: 30 mins.
*   **Seed Phase**: 45 mins.
*   **Adaptive Loops**: 4 bursts $\times$ 60 mins = 4 hours.
    *   *Mining is CPU-bound*: Use fast string matching or `tokenizers` library, not raw Python loops.
*   **Evaluation**: 45 mins.
*   **Buffer**: ~1.5 hours.

## 5. Feasibility & Risks
*   **Risk**: CPU bottleneck during candidate mining.
    *   *Mitigation*: Mine only on a "buffer" of the last 1M tokens, not the whole corpus.
*   **Risk**: OOM during embedding resizing.
    *   *Mitigation*: Use LoRA. The embedding matrix growth (2000 tokens $\times$ 4096 dim) is only ~32MB. Negligible.

