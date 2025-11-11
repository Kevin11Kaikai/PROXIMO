# Temperature Control in LLM: PPT Slide Content

## Slide Title
**How Temperature Controls LLM Flexibility**

---

## Key Points (3-4 sentences)

**Temperature controls randomness in LLM text generation by scaling the probability distribution.**

- **Low Temperature (0.1-0.3)**: Sharpens probability distribution → more deterministic, consistent responses
- **High Temperature (0.8-1.0)**: Flattens probability distribution → more diverse, creative responses

**Formula**: `P(i) = exp(logit(i) / T) / Σ exp(logit(j) / T)`

**Lower T = sharper distribution = less flexibility | Higher T = flatter distribution = more flexibility**

---

## Table: Temperature Effects on LLM Behavior

| Temperature | Probability Distribution | Response Style | Flexibility | Use Case |
|------------|-------------------------|----------------|-------------|----------|
| **0.1** | Very Sharp (nearly deterministic) | Consistent, predictable | **Low** | High-risk scenarios (safety-critical) |
| **0.3** | Sharp (high confidence) | Structured, reliable | **Low-Medium** | Medium-risk (semi-structured) |
| **0.6** | Moderate | Balanced, controlled | **Medium** | Medium-risk (semi-structured) |
| **0.9** | Flat (more random) | Diverse, natural | **High** | Low-risk (free conversation) |

---

## Alternative: Simplified Table (More Visual)

| Temperature | Distribution Shape | Flexibility Level | Example Behavior |
|------------|-------------------|-------------------|------------------|
| **0.1** | ████████████████ (Sharp) | **Low** | Always selects most likely word |
| **0.3** | ████████████░░░░ (Sharp) | **Low-Med** | Prefers high-probability words |
| **0.6** | ████████░░░░░░░░ (Moderate) | **Medium** | Balances certainty and variety |
| **0.9** | ████░░░░░░░░░░░░ (Flat) | **High** | More likely to choose less probable words |

---

## One-Line Summary (For Bullet Point)

**Temperature scales logit values before softmax: lower T → sharper distribution → less flexibility; higher T → flatter distribution → more flexibility.**

---

## Mathematical Intuition (Optional)

**Key Formula:**
```
P(word) = exp(logit / T) / Σ exp(logit_j / T)
```

**Effect:**
- **T → 0**: Distribution becomes peaked (deterministic)
- **T → ∞**: Distribution becomes uniform (random)

---

## Visual Concept (For Diagram)

```
Low Temperature (T=0.1):
Probability:  ████████████████░░░░  (Sharp peak)
              Word A (0.999) dominates

High Temperature (T=0.9):
Probability:  ████░░░░░░░░░░░░░░░░  (Flat)
              Words A, B, C have similar chances
```

---

## Complete Slide Text (Concise Version)

### Title
**Temperature: Controlling LLM Flexibility**

### Body

**What is Temperature?**
Temperature scales the probability distribution in LLM text generation.

**How it works:**
- **Low T (0.1-0.3)**: Sharpens distribution → deterministic, consistent responses
- **High T (0.8-1.0)**: Flattens distribution → diverse, creative responses

**Formula:** `P(i) = exp(logit(i)/T) / Σ exp(logit(j)/T)`

**Table:**

| T | Distribution | Flexibility | Use Case |
|---|-------------|-------------|----------|
| 0.1 | Sharp | Low | High-risk (safety) |
| 0.6 | Moderate | Medium | Medium-risk |
| 0.9 | Flat | High | Low-risk (free chat) |

**Bottom line:** Lower T = more rigid, Higher T = more flexible

---

## PowerPoint-Friendly Format

### Slide 1: Title Slide
**Temperature Control in LLM Generation**

### Slide 2: Explanation
**Temperature scales probability distribution**

- Low T → Sharp distribution → Deterministic
- High T → Flat distribution → Random

**Formula:** `P = exp(logit/T) / Σ exp(logit/T)`

### Slide 3: Table
**Temperature Effects**

| Temperature | Flexibility | Response Style |
|------------|-------------|----------------|
| 0.1 | Low | Consistent, predictable |
| 0.6 | Medium | Balanced |
| 0.9 | High | Diverse, creative |

### Slide 4: Application (Our Project)
**Rigid Score → Temperature Mapping**

- High Risk (rigid_score=1.0) → T=0.1 → Fixed script
- Medium Risk (rigid_score=0.6) → T=0.4 → Semi-structured
- Low Risk (rigid_score=0.15) → T=0.9 → Free conversation

---

## Key Takeaways (Bullet Points)

1. **Temperature controls randomness** in LLM generation
2. **Lower T** = sharper probability distribution = **less flexibility**
3. **Higher T** = flatter probability distribution = **more flexibility**
4. **Mathematical formula**: `P = exp(logit/T) / Σ exp(logit/T)`
5. **Application**: Adjust T based on risk level (safety vs. creativity trade-off)

