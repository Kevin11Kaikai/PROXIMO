# Temperature Control in Next Token Prediction: PPT Slide Content

## Slide 1: Title
**How Temperature Controls LLM Flexibility in Next Token Prediction**

---

## Slide 2: Next Token Prediction Process

### Title
**How LLM Generates the Next Token**

### Content

**Step 1: Input Processing**
```
User: "I feel sad"
→ LLM processes input sequence
```

**Step 2: Model Outputs Logits**
```
LLM generates logits (raw scores) for each candidate token:
Token "understand" → logit = 2.5
Token "hear"      → logit = 2.3
Token "see"       → logit = 1.8
Token "feel"      → logit = 1.5
...
Token "happy"     → logit = 0.1
```

**Step 3: Apply Temperature Scaling**
```
P(token) = exp(logit / T) / Σ exp(logit / T)
```

**Step 4: Sample Next Token**
```
Select token based on probability distribution
```

---

## Slide 3: Concrete Example - Next Token Prediction

### Title
**Example: Predicting Next Token After "I feel"**

### Scenario
**Input**: "I feel"
**Candidate tokens**: "sad", "happy", "anxious", "better"

### Table: Logits and Probabilities

| Token | Logit | Temperature = 0.1 | Temperature = 1.0 | Temperature = 2.0 |
|-------|-------|-------------------|-------------------|-------------------|
| **sad** | 2.5 | **0.999** | **0.659** | **0.500** |
| happy | 1.0 | 0.001 | 0.242 | 0.327 |
| anxious | 0.5 | 0.000 | 0.083 | 0.135 |
| better | 0.1 | 0.000 | 0.016 | 0.038 |

### Key Observation
- **Low T (0.1)**: "sad" dominates (99.9% probability)
- **High T (2.0)**: All tokens have more balanced probabilities

---

## Slide 4: Mathematical Calculation

### Title
**Temperature Scaling: Step-by-Step Calculation**

### Example: Token "sad" with logit = 2.5

**Step 1: Scale logits by temperature**
```
scaled_logit = logit / T
```

**Step 2: Apply exponential**
```
exp_scaled = exp(scaled_logit)
```

**Step 3: Calculate probabilities**
```
P(token) = exp_scaled / Σ(exp_scaled for all tokens)
```

### Calculation Table

| Temperature | Scaled Logit | exp(scaled) | Probability |
|------------|--------------|-------------|-------------|
| **T = 0.1** | 2.5 / 0.1 = 25.0 | exp(25.0) ≈ 7.2×10¹⁰ | **0.999** |
| **T = 1.0** | 2.5 / 1.0 = 2.5 | exp(2.5) ≈ 12.18 | **0.659** |
| **T = 2.0** | 2.5 / 2.0 = 1.25 | exp(1.25) ≈ 3.49 | **0.500** |

**Note**: Denominator (normalization) changes with temperature, affecting all tokens proportionally.

---

## Slide 5: Visual Comparison

### Title
**Probability Distribution: Temperature Effects**

### Visualization

**Input**: "I feel"
**Top 4 candidate tokens**: sad (2.5), happy (1.0), anxious (0.5), better (0.1)

#### Temperature = 0.1 (Low)
```
Probability Distribution:
sad:     ████████████████████████████████████ 99.9%
happy:   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.1%
anxious: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.0%
better:  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0.0%

Result: Almost always selects "sad" (deterministic)
```

#### Temperature = 1.0 (Standard)
```
Probability Distribution:
sad:     ████████████████████████░░░░░░░░░░  65.9%
happy:   ██████████░░░░░░░░░░░░░░░░░░░░░░░  24.2%
anxious: ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   8.3%
better:  █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   1.6%

Result: Mostly "sad", but other tokens possible
```

#### Temperature = 2.0 (High)
```
Probability Distribution:
sad:     ████████████████████░░░░░░░░░░░░░░  50.0%
happy:   ██████████████░░░░░░░░░░░░░░░░░░░  32.7%
anxious: ████████░░░░░░░░░░░░░░░░░░░░░░░░░  13.5%
better:  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   3.8%

Result: More balanced, more variety possible
```

---

## Slide 6: Real-World Example

### Title
**Complete Example: Generating Response**

### Scenario
**User**: "I've been feeling really anxious lately."

### Next Token Prediction (First Token)

**Candidate tokens after "I've been feeling really anxious":**
- "and" (logit: 1.8)
- "about" (logit: 1.5)
- "because" (logit: 1.2)
- "so" (logit: 0.8)
- "but" (logit: 0.5)

### Table: Temperature Effects on First Token

| Temperature | Most Likely Token | Probability | Flexibility |
|------------|-------------------|-------------|-------------|
| **0.1** | "and" | 0.95 | Low (deterministic) |
| **0.6** | "and" | 0.65 | Medium |
| **0.9** | "and" | 0.45 | High (varied) |

### Generated Responses

**T = 0.1** (Low):
```
"I've been feeling really anxious and I don't know what to do."
→ Consistent, predictable response
```

**T = 0.9** (High):
```
"I've been feeling really anxious about school lately."
OR
"I've been feeling really anxious so I reached out for help."
→ More diverse, natural variations
```

---

## Slide 7: Sampling Process

### Title
**From Probability to Token Selection**

### Process Flow

```
1. Calculate probabilities using temperature
   P("sad") = 0.659, P("happy") = 0.242, P("anxious") = 0.083, ...

2. Sample from distribution
   Method: Multinomial sampling
   
3. Select token based on sample
```

### Example: 10 Sampling Trials

**Temperature = 0.1:**
```
Trial 1: sad
Trial 2: sad
Trial 3: sad
Trial 4: sad
Trial 5: sad
...
Result: "sad" selected 10/10 times (100%)
```

**Temperature = 1.0:**
```
Trial 1: sad
Trial 2: sad
Trial 3: happy
Trial 4: sad
Trial 5: sad
Trial 6: anxious
...
Result: "sad" selected 7/10 times (70%), "happy" 2/10 (20%), "anxious" 1/10 (10%)
```

**Temperature = 2.0:**
```
Trial 1: sad
Trial 2: happy
Trial 3: sad
Trial 4: happy
Trial 5: anxious
Trial 6: sad
...
Result: More diverse selection, closer to probability distribution
```

---

## Slide 8: Complete Generation Example

### Title
**Full Response Generation: Temperature Impact**

### Input
**User**: "I feel"

### Generation Process (Token by Token)

#### Temperature = 0.1 (Low Flexibility)

```
Step 1: "I feel" → Next token: "sad" (P=0.999)
Step 2: "I feel sad" → Next token: "today" (P=0.95)
Step 3: "I feel sad today" → Next token: "because" (P=0.92)
Step 4: "I feel sad today because" → Next token: "of" (P=0.88)
...

Final Response: "I feel sad today because of what happened."
→ Predictable, consistent structure
```

#### Temperature = 0.9 (High Flexibility)

```
Step 1: "I feel" → Next token: "sad" (P=0.45) OR "anxious" (P=0.30) OR "better" (P=0.15)
Step 2: (If "sad") → Next token: "lately" (P=0.40) OR "sometimes" (P=0.35)
Step 3: (If "sad lately") → Next token: "and" (P=0.38) OR "but" (P=0.32)
...

Possible Responses:
- "I feel sad lately and don't know why."
- "I feel anxious about the exam tomorrow."
- "I feel better when I talk to someone."
→ Diverse, natural variations
```

---

## Slide 9: Key Takeaways

### Title
**Temperature in Next Token Prediction: Summary**

### Key Points

1. **LLM generates logits** for each candidate token
2. **Temperature scales logits** before softmax: `P = exp(logit/T) / Σ exp(logit/T)`
3. **Low T** → Sharp distribution → **Deterministic** next token
4. **High T** → Flat distribution → **Diverse** next token selection
5. **Repeated for each token** → Cumulative effect on response flexibility

### Formula
```
Next Token Probability = exp(logit(token) / T) / Σ exp(logit(all_tokens) / T)
```

### Application
- **Low T (0.1)**: Predictable, safe responses (high-risk scenarios)
- **High T (0.9)**: Creative, natural responses (low-risk scenarios)

---

## Slide 10: Practical Example Table

### Title
**Temperature Effects: Complete Example**

### Input Context
**User**: "I've been struggling with"

### Next Token Prediction

| Candidate Token | Logit | T=0.1 | T=0.6 | T=0.9 | Selected? (T=0.1) | Selected? (T=0.9) |
|----------------|-------|-------|-------|-------|-------------------|-------------------|
| **anxiety** | 2.8 | 0.995 | 0.750 | 0.550 | ✅ Always | ✅ Often |
| stress | 2.0 | 0.004 | 0.180 | 0.280 | ❌ Rarely | ✅ Sometimes |
| depression | 1.5 | 0.001 | 0.050 | 0.120 | ❌ Never | ✅ Occasionally |
| school | 1.0 | 0.000 | 0.015 | 0.040 | ❌ Never | ✅ Rarely |
| work | 0.5 | 0.000 | 0.005 | 0.010 | ❌ Never | ❌ Rarely |

### Generated Responses

**T = 0.1**: 
- "I've been struggling with **anxiety** lately."
- (99.5% chance of "anxiety")

**T = 0.9**: 
- "I've been struggling with **anxiety** about exams."
- OR "I've been struggling with **stress** from work."
- OR "I've been struggling with **depression** recently."
- (More variety, 55% "anxiety", 28% "stress", 12% "depression")

---

## Slide 11: Code Example (Optional)

### Title
**Python Implementation**

### Code Snippet

```python
import numpy as np

def predict_next_token(logits, temperature=1.0):
    """
    Predict next token using temperature scaling.
    
    Args:
        logits: Array of logit scores for each candidate token
        temperature: Temperature parameter (T > 0)
    
    Returns:
        Selected token index
    """
    # Step 1: Scale logits by temperature
    scaled_logits = logits / temperature
    
    # Step 2: Apply softmax
    exp_logits = np.exp(scaled_logits)
    probabilities = exp_logits / np.sum(exp_logits)
    
    # Step 3: Sample from distribution
    token_index = np.random.choice(len(logits), p=probabilities)
    
    return token_index, probabilities

# Example
logits = np.array([2.5, 1.0, 0.5, 0.1])  # 4 candidate tokens
tokens = ["sad", "happy", "anxious", "better"]

# Low temperature
token_idx, probs = predict_next_token(logits, temperature=0.1)
print(f"T=0.1: Selected '{tokens[token_idx]}' (P={probs[token_idx]:.3f})")
# Output: T=0.1: Selected 'sad' (P=0.999)

# High temperature
token_idx, probs = predict_next_token(logits, temperature=2.0)
print(f"T=2.0: Selected '{tokens[token_idx]}' (P={probs[token_idx]:.3f})")
# Output: T=2.0: Selected 'sad' (P=0.500) or 'happy' (P=0.327)
```

---

## Slide 12: Complete Flow Diagram

### Title
**Next Token Prediction: Complete Flow**

### Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Input Processing                                 │
│ "I feel" → Tokenize → Embed → Process                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2: Model Generates Logits                          │
│ Token "sad"    → logit = 2.5                            │
│ Token "happy"  → logit = 1.0                            │
│ Token "anxious" → logit = 0.5                           │
│ ...                                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3: Apply Temperature Scaling                       │
│ P(i) = exp(logit(i) / T) / Σ exp(logit(j) / T)         │
│                                                          │
│ T=0.1: P("sad") = 0.999                                 │
│ T=1.0: P("sad") = 0.659                                 │
│ T=2.0: P("sad") = 0.500                                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 4: Sample Next Token                               │
│ T=0.1: Select "sad" (deterministic)                     │
│ T=1.0: Select "sad" (likely) or "happy" (possible)     │
│ T=2.0: Select any token (more random)                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ Step 5: Repeat for Next Token                           │
│ "I feel sad" → Predict next token → "I feel sad today"  │
│ Continue until end of response                          │
└─────────────────────────────────────────────────────────┘
```

---

## Slide 13: Comparison Table (Final)

### Title
**Temperature Control: Complete Comparison**

### Table

| Aspect | Low Temperature (T=0.1) | High Temperature (T=0.9) |
|--------|------------------------|-------------------------|
| **Next Token Selection** | Almost always highest logit | More diverse selection |
| **Probability Distribution** | Sharp peak (99.9% for top token) | Flatter (45-30-15% for top tokens) |
| **Response Variety** | Low (predictable) | High (diverse) |
| **Use Case** | High-risk (safety-critical) | Low-risk (natural conversation) |
| **Example** | "I feel sad" (99.9% chance) | "I feel sad/anxious/better" (varied) |
| **Flexibility** | **Low** | **High** |

### Formula
```
P(token) = exp(logit / T) / Σ exp(logit / T)
```

### Key Insight
**Temperature controls the "randomness" in next token selection, which accumulates over multiple tokens to create response flexibility.**

---

## Recommended Slide Order for Presentation

1. **Slide 1**: Title - "How Temperature Controls LLM Flexibility"
2. **Slide 2**: Next Token Prediction Process (overview)
3. **Slide 3**: Concrete Example - "I feel" → next token
4. **Slide 5**: Visual Comparison (probability distributions)
5. **Slide 6**: Real-World Example (complete response)
6. **Slide 8**: Complete Generation Example (token by token)
7. **Slide 13**: Comparison Table (summary)
8. **Slide 9**: Key Takeaways

---

## Quick Reference: One-Slide Summary

### Title
**Temperature in Next Token Prediction**

### Content

**Process:**
1. LLM generates **logits** for candidate tokens
2. Apply **temperature scaling**: `P = exp(logit/T) / Σ exp(logit/T)`
3. **Sample** next token from probability distribution
4. **Repeat** for each token in response

**Example: "I feel" → Next token?**
- **T=0.1**: "sad" (99.9% probability) → Deterministic
- **T=0.9**: "sad" (45%), "happy" (30%), "anxious" (15%) → Diverse

**Effect:**
- **Low T** → Sharp distribution → **Less flexibility**
- **High T** → Flat distribution → **More flexibility**

