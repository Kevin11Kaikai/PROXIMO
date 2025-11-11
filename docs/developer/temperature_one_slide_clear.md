# Temperature 影响 Next Token Prediction - 单页清晰版

## 核心问题

**Temperature 不同会造成 next token prediction 的不同吗？**

**答案：是的！**

---

## 单页 Slide：清晰版本

### 标题
**Does Temperature Affect Next Token Prediction? YES!**

---

### 内容

**Key Point:** Temperature changes the probability distribution, which changes the next token prediction.

**Process:**
```
Fixed Logits → [Temperature Scaling] → Different Probabilities → Different Predictions
```

**Example: "I feel" → Next token?**

| Token | Logit (Fixed) | T=0.1 Probability | T=2.0 Probability | Will be Selected? (T=0.1) | Will be Selected? (T=2.0) |
|-------|--------------|-------------------|-------------------|---------------------------|---------------------------|
| **sad** | 2.5 | **99.9%** | **50.0%** | ✅ Yes (almost always) | ✅ Yes (often) |
| happy | 1.0 | 0.1% | 32.7% | ❌ No (rarely) | ✅ Yes (sometimes) |
| anxious | 0.5 | 0.0% | 13.5% | ❌ No (never) | ✅ Yes (occasionally) |

**Key Insight:**
- **Same logits** (model output is fixed)
- **Different probabilities** (temperature changes distribution)
- **Different predictions** (sampling from different distributions)

**Formula:** `P(token) = exp(logit / T) / Σ exp(logit / T)`

**Answer:** YES, temperature affects next token prediction by changing the probability distribution used for sampling.

---

## 更简洁的单页版本

### 标题
**Temperature Changes Next Token Prediction**

---

### 内容

**Question:** Does temperature affect next token prediction?

**Answer: YES!**

**Why:**
1. Logits are **fixed** (model output)
2. Temperature changes **probability distribution**
3. Different probabilities → Different sampling → **Different predictions**

**Example: "I feel" → Next token?**

| Token | Logit | T=0.1 | T=2.0 | Will be Selected? (T=0.1) | Will be Selected? (T=2.0) |
|-------|-------|-------|-------|---------------------------|---------------------------|
| sad | 2.5 | 99.9% | 50.0% | ✅ Yes (almost always) | ✅ Yes (often) |
| happy | 1.0 | 0.1% | 32.7% | ❌ No (rarely) | ✅ Yes (sometimes) |
| anxious | 0.5 | 0.0% | 13.5% | ❌ No (never) | ✅ Yes (occasionally) |

**Key:** Same logits → Different T → Different probabilities → **Different next token prediction**

---

## 因果关系图（单页）

### 标题
**How Temperature Affects Next Token Prediction**

---

### 内容

**Causal Chain:**
```
Temperature (T)
    ↓
Probability Distribution: P = exp(logit/T) / Σ exp(logit/T)
    ↓
Sampling Process
    ↓
Next Token Prediction
```

**Example: "I feel" → Next token?**

| Step | T=0.1 | T=2.0 |
|------|-------|-------|
| **Logits** (Fixed) | sad: 2.5, happy: 1.0, anxious: 0.5 | sad: 2.5, happy: 1.0, anxious: 0.5 |
| **Probabilities** | sad: 99.9%, happy: 0.1%, anxious: 0.0% | sad: 50.0%, happy: 32.7%, anxious: 13.5% |
| **Prediction** | ✅ Always "sad" | ✅ "sad" (50%), "happy" (33%), or "anxious" (14%) |

**Conclusion:** Different T → Different probabilities → **Different next token prediction**

---

## 最清晰的单页版本（推荐）

### 标题
**Temperature Changes Next Token Prediction**

---

### 内容

**Key Question:** Does temperature affect next token prediction?

**Answer: YES!**

**Mechanism:**
```
Temperature → Probability Distribution → Sampling → Next Token
```

**What stays the same:**
- Logits (model output): sad=2.5, happy=1.0, anxious=0.5

**What changes:**
- Probability distribution (depends on T)
- Next token prediction (depends on probabilities)

**Example: "I feel" → Next token?**

| Token | Logit | T=0.1 | T=2.0 | Result |
|-------|-------|-------|-------|--------|
| sad | 2.5 | 99.9% | 50.0% | T=0.1: Always "sad" |
| happy | 1.0 | 0.1% | 32.7% | T=2.0: May be "happy" |
| anxious | 0.5 | 0.0% | 13.5% | T=2.0: May be "anxious" |

**Formula:** `P = exp(logit/T) / Σ exp(logit/T)`

**Conclusion:** Different temperature → Different probabilities → **Different next token prediction**

---

## PowerPoint 直接使用版本

### Slide Title
**Temperature Changes Next Token Prediction**

### Slide Body

**Question:** Does temperature affect next token prediction?

**Answer: YES!**

**Mechanism:**
```
Temperature → Probability Distribution → Sampling → Next Token
```

**Example: "I feel" → Next token?**

| Token | Logit (Fixed) | T=0.1 | T=2.0 | Will be Selected? |
|-------|--------------|-------|-------|-------------------|
| sad | 2.5 | 99.9% | 50.0% | T=0.1: ✅ Yes (almost always) |
| happy | 1.0 | 0.1% | 32.7% | T=2.0: ✅ Yes (sometimes) |
| anxious | 0.5 | 0.0% | 13.5% | T=2.0: ✅ Yes (occasionally) |

**Key Points:**
- Logits are **fixed** (model output)
- Temperature changes **probabilities**
- Different probabilities → **Different predictions**

**Formula:** `P = exp(logit/T) / Σ exp(logit/T)`

**Conclusion:** Different T → Different next token prediction

