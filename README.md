# 🧠 PROXIMO — Controllable and Ethically Aligned Mental Health Chatbot for Adolescents

## 🎯 Core Objective

**PROXIMO** aims to build a controllable, ethically aligned, LLM-based mental health dialogue system for adolescents.  
It can:
1. Detect and assess **mental health risk levels** (e.g., suicide, anxiety, depression).  
2. Dynamically adjust **dialogue flexibility and intervention strength** based on risk level.  
3. Provide **supportive conversations, clinical assessments, and crisis referrals** safely and empathetically.

> “An AI companion that knows the boundaries of safety, but still speaks with warmth.”

---

## 🧩 System Architecture — Multi-Agent Mental Health Chatbot Framework

| Layer | Agent / Module | Function |
|-------|----------------|-----------|
| **A. Perception Layer** | Risk Evaluation Agent | Detects emotional and linguistic signals of distress (e.g., suicidal ideation, self-blame, negative affect). |
| **B. Reasoning & Control Layer** | Controller / Risk Router | Maps risk score \(S \in [0,1]\) → Low / Medium / High, adjusts chatbot’s freedom accordingly. |
| **C. Conversation Layer** | Coping / Peer Support / Crisis Intervention Agents  | Low risk → free empathetic chat;<br>Medium risk → semi-structured peer-support guidance;<br>High risk → structured safety prompts |
| **D. Safety & Ethics Layer** | Guardrails + Ethical Filter | Nemo Guardrails / LlamaGuard ensure compliance, prevent unsafe responses. |
| **E. Adaptive Layer** | Memory & Feedback Agent | Evaluates outcomes and adapts to user needs. |

---

## 💬 Conversation Flow (Wireframe Summary)

### 🧠 Low Risk
- Chatbot engages freely, explores emotions and stress sources.  
- Triggers **GAD-7** conversationally if mild anxiety detected.  
- Offers **coping strategies** and positive reframing.  
- **High temperature (≈ 0.9)** → empathetic and open.

### ⚖️ Medium Risk
- Detects moderate anxiety/depression signals.  
- Encourages user to join a **Peer Support Group**, handles hesitation.  
- Reinforces community connection.  
- **Moderate temperature (≈ 0.6)** → semi-structured control.

### 🚨 High Risk
- Detects suicidal language or severe emotional distress.  
- Initiates **C-SSRS** screening and shows **988 Crisis Hotline**.  
- Ends open conversation and transitions to safety protocol.  
- **Low temperature (≈ 0.2)** → structured, deterministic.

---

## 🧮 Risk Evaluation Mechanism

| Range | Risk Level | Chatbot Behavior |
|--------|-------------|------------------|
| (S < 0.3) | Low | Free empathetic dialogue + coping skills |
| (0.3 ≤ S < 0.7) | Medium | Semi-structured peer support guidance |
| (S ≥ 0.7) | High | Structured C-SSRS flow + crisis referral |

---

## ⚙️ Technical Stack

| Module | Technology |
|---------|-------------|
| **Dialogue Generation** | GPT-4 / GPT-4o + psychological prompts |
| **Retrieval Augmentation** | LangChain RAG (clinical scales + coping corpus) |
| **Control Layer** | Nemo Guardrails / LlamaGuard |
| **Data** | Reddit Suicide_Detection, DeepSuiMind, PsySUICIDE, SMHD, PsyQA |
| **Multi-Agent Framework** | Supervisor, Risk Evaluator, Chat, and Ethics Agents |
| **UI Prototype** | Discord-like / Instagram-like (IDEA Lab design) |

---

## 🧭 Research and Application Goals

| Dimension | Focus |
|------------|--------|
| 🎓 **Scientific** | Explore controllability, interpretability, and ethical alignment of LLMs in mental health contexts. |
| 🧑‍💻 **Engineering** | Build a safe, measurable dialogue engine integrating RAG, Guardrails, and multi-agent design. |
| 💬 **Clinical** | Evaluate effectiveness of AI in adolescent emotional support and risk triage. |
| 📈 **Long-Term** | Develop a “controllable, ethical mental health AI ecosystem” for IRB and NIH research. |

---

## 📊 Current Progress (as of Nov 2025)

| Module | Status |
|---------|--------|
| ✅ Wireframes (Low/Medium/High) | Reviewed by IDEA Lab |
| ✅ Risk Evaluation Model | Implemented continuous suicide risk score (S ∈ [0,1]) |
| ⚙️ Chatbot Prototype | Under active development (Guardrails + RAG + LangChain) |
| 🧠 AI-Psychology Multi-Agent System | Expanding with Supervisor / Patient / Doctor / Reframing agents |
| 📈 Research Collaboration | Preparing IRB protocol & AHRQ/NIH proposals |

---

## 🧠 Summary

> **PROXIMO = Safe, Controllable, and Warm AI for Adolescent Mental Health.**  
> It’s not just a chatbot — it’s a measurable, ethical AI ecosystem for emotional well-being.
