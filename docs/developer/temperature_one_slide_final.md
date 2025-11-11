# Temperature Control: One-Slide Final Version (Updated Column Names)

## Single Slide: Complete and Clear

### Title
**Temperature Changes Next Token Prediction**

---

### Content

**Question:** Does temperature affect next token prediction?

**Answer: YES!**

**Mechanism:**
```
Temperature → Probability Distribution → Sampling → Next Token
```

**Example: "I feel" → Next token?**

| Token | Logit (Fixed) | T=0.1 Probability | T=2.0 Probability | Will be Selected? (T=0.1) | Will be Selected? (T=2.0) |
|-------|--------------|-------------------|-------------------|---------------------------|---------------------------|
| **sad** | 2.5 | **99.9%** | **50.0%** | ✅ Yes (almost always) | ✅ Yes (often) |
| happy | 1.0 | 0.1% | 32.7% | ❌ No (rarely) | ✅ Yes (sometimes) |
| anxious | 0.5 | 0.0% | 13.5% | ❌ No (never) | ✅ Yes (occasionally) |

**Key Points:**
- **Logits are fixed** (model output doesn't change)
- **Temperature changes probabilities** (P = exp(logit/T) / Σ exp(logit/T))
- **Different probabilities → Different predictions**

**Formula:** `P = exp(logit/T) / Σ exp(logit/T)`

**Conclusion:** Different temperature → Different next token prediction

---

## PowerPoint Ready Version

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

| Token | Logit (Fixed) | T=0.1 | T=2.0 | Will be Selected? (T=0.1) | Will be Selected? (T=2.0) |
|-------|--------------|-------|-------|---------------------------|---------------------------|
| **sad** | 2.5 | **99.9%** | **50.0%** | ✅ Yes (almost always) | ✅ Yes (often) |
| happy | 1.0 | 0.1% | 32.7% | ❌ No (rarely) | ✅ Yes (sometimes) |
| anxious | 0.5 | 0.0% | 13.5% | ❌ No (never) | ✅ Yes (occasionally) |

**Key Points:**
- Logits are **fixed** (model output)
- Temperature changes **probabilities**
- Different probabilities → **Different predictions**

**Formula:** `P = exp(logit/T) / Σ exp(logit/T)`

**Conclusion:** Different T → Different next token prediction

---

## Column Name Explanation

**"Will be Selected? (T=0.1)" 列的含义：**

- ✅ **Yes (almost always)**: 在 T=0.1 时，几乎总是（99.9% 的概率）选择这个 token
- ✅ **Yes (often)**: 在 T=2.0 时，经常（50% 的概率）选择这个 token
- ✅ **Yes (sometimes)**: 在 T=2.0 时，有时（33% 的概率）选择这个 token
- ✅ **Yes (occasionally)**: 在 T=2.0 时，偶尔（14% 的概率）选择这个 token
- ❌ **No (rarely)**: 在 T=0.1 时，很少（0.1% 的概率）选择这个 token
- ❌ **No (never)**: 在 T=0.1 时，从不（0.0% 的概率）选择这个 token

**这一列明确回答了：在给定的 temperature 下，这个 token 是否会被选为下一个 token。**

