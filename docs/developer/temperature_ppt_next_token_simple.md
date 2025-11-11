# Temperature Control: Next Token Prediction (PPT Version)

## Slide Content: Next Token Prediction with Temperature

### Title
**How Temperature Controls Next Token Prediction**

---

### Key Explanation (2-3 sentences)

**LLM generates logits (raw scores) for each candidate token, then applies temperature scaling to create a probability distribution.**
- **Low Temperature (0.1)**: Sharpens distribution → almost always selects highest logit token (deterministic)
- **High Temperature (0.9)**: Flattens distribution → allows selection of lower logit tokens (diverse)

**Formula**: `P(token) = exp(logit / T) / Σ exp(logit / T)`

---

### Main Table: Next Token Prediction Example

**Context**: User says **"I feel"**
**Question**: What's the next token?

| Candidate Token | Logit | T=0.1 (Low) | T=1.0 (Standard) | T=2.0 (High) | Will be Selected? (T=0.1) | Will be Selected? (T=2.0) |
|----------------|-------|-------------|------------------|--------------|---------------------------|---------------------------|
| **sad** | 2.5 | **0.999** | **0.659** | **0.500** | ✅ Yes (almost always, 99.9%) | ✅ Yes (often, 50%) |
| happy | 1.0 | 0.001 | 0.242 | 0.327 | ❌ No (rarely, 0.1%) | ✅ Yes (sometimes, 33%) |
| anxious | 0.5 | 0.000 | 0.083 | 0.135 | ❌ No (never, 0%) | ✅ Yes (occasionally, 14%) |
| better | 0.1 | 0.000 | 0.016 | 0.038 | ❌ No (never, 0%) | ❌ No (rarely, 4%) |

**Result:**
- **T=0.1**: "sad" selected 99.9% of the time → **Deterministic response**
- **T=2.0**: "sad" (50%), "happy" (33%), "anxious" (14%) → **Diverse responses**

---

### Visual Comparison (Optional Diagram)

```
Input: "I feel"
Next Token Prediction:

T=0.1 (Low):
  sad:     ████████████████████████████████████ 99.9%
  happy:   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.1%
  anxious: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.0%

T=2.0 (High):
  sad:     ████████████████████░░░░░░░░░░░░░░  50.0%
  happy:   ██████████████░░░░░░░░░░░░░░░░░░░  32.7%
  anxious: ████████░░░░░░░░░░░░░░░░░░░░░░░░░  13.5%
  better:  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3.8%
```

---

### Process Flow (Simple)

```
Step 1: Model generates logits
  "I feel" → [sad: 2.5, happy: 1.0, anxious: 0.5, better: 0.1]

Step 2: Apply temperature scaling
  P(token) = exp(logit / T) / Σ exp(logit / T)

Step 3: Sample next token
  T=0.1 → Select "sad" (99.9% chance)
  T=2.0 → Select "sad" (50%), "happy" (33%), or "anxious" (14%)

Step 4: Repeat for each token
  "I feel sad" → Predict next token → "I feel sad today" → ...
```

---

### Complete Example: Full Response Generation

**Input**: "I feel"

**T=0.1 (Low Flexibility):**
```
Token 1: "sad" (P=0.999) → "I feel sad"
Token 2: "today" (P=0.95) → "I feel sad today"
Token 3: "because" (P=0.92) → "I feel sad today because"
...
Final: "I feel sad today because of what happened."
→ Predictable, consistent
```

**T=0.9 (High Flexibility):**
```
Token 1: "sad" (P=0.45) OR "anxious" (P=0.30) OR "better" (P=0.15)
Token 2: (varies based on token 1)
Token 3: (varies based on context)
...
Possible Responses:
- "I feel sad lately and don't know why."
- "I feel anxious about the exam."
- "I feel better when I talk to someone."
→ Diverse, natural variations
```

---

### Key Takeaways (Bullet Points)

1. **LLM predicts next token** by generating logits for each candidate
2. **Temperature scales logits** before softmax: `P = exp(logit/T) / Σ exp(logit/T)`
3. **Low T** → Sharp distribution → **Deterministic** next token (always highest logit)
4. **High T** → Flat distribution → **Diverse** next token (multiple possibilities)
5. **Repeated for each token** → Cumulative effect creates response flexibility
6. **Lower T = less flexibility | Higher T = more flexibility**

---

## One-Slide Summary (Recommended)

### Title
**Temperature in Next Token Prediction**

### Content

**Process:**
1. LLM generates **logits** for candidate tokens
2. Apply **temperature**: `P = exp(logit/T) / Σ exp(logit/T)`
3. **Sample** next token from probability distribution
4. **Repeat** for each token

**Example: "I feel" → Next token?**

| Token | Logit | T=0.1 | T=2.0 |
|-------|-------|-------|-------|
| **sad** | 2.5 | **99.9%** | **50.0%** |
| happy | 1.0 | 0.1% | 32.7% |
| anxious | 0.5 | 0.0% | 13.5% |

**Effect:**
- **T=0.1**: Always "sad" → Deterministic
- **T=2.0**: "sad" (50%), "happy" (33%), "anxious" (14%) → Diverse

**Key Insight:** Temperature controls randomness in next token selection, which accumulates over multiple tokens to create response flexibility.

---

## PowerPoint Slide Structure

### Slide 1: Title
**Temperature Control in Next Token Prediction**

### Slide 2: Process Overview
**How LLM Predicts Next Token:**
1. Generate logits for candidate tokens
2. Apply temperature scaling
3. Sample from probability distribution
4. Repeat for each token

### Slide 3: Concrete Example (Main Table)
**Example: "I feel" → Next token?**

[Insert the main table above]

### Slide 4: Visual Comparison
**Probability Distribution:**

[Insert visual comparison diagram]

### Slide 5: Key Takeaways
**Summary:**
- Low T → Sharp distribution → Deterministic
- High T → Flat distribution → Diverse
- Formula: `P = exp(logit/T) / Σ exp(logit/T)`

---

## Quick Reference Card

**Temperature in Next Token Prediction**

**Formula:** `P(token) = exp(logit / T) / Σ exp(logit / T)`

**Effect:**
- **T → 0**: Distribution becomes peaked → Deterministic selection
- **T → ∞**: Distribution becomes uniform → Random selection

**Example:**
- **T=0.1**: "sad" (99.9%) → Always selects highest logit
- **T=2.0**: "sad" (50%), "happy" (33%) → More variety

**Application:**
- Low T (0.1) → High-risk scenarios (safety-critical)
- High T (0.9) → Low-risk scenarios (natural conversation)

