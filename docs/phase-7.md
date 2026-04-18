# Phase 7: Adaptive Behaviour

## Overview

**Coding:** Required
**Tools/Skills:** Feedback collection, memory management (short-term & long-term), behavior adaptation, prompt engineering, multi-turn evaluation

In this phase, the agent is enhanced with **adaptive behavior and memory awareness**, enabling it to:

- Learn from user feedback
- Persist preferences across sessions
- Maintain short-term conversational context
- Adjust responses dynamically

This phase introduces **true personalization** by combining **feedback-driven adaptation + memory handling**.

---

## Objective

- Introduce feedback signals
- Store feedback for future interactions
- Modify behavior dynamically
- Add short-term conversational memory
- Demonstrate before vs after behavior
- Define memory boundaries (reset vs persistence)

---

## Implementation

The system is implemented with **two types of memory**:

### 1. Short-Term Memory (Session Context)

### 2. Long-Term Memory (User Preferences)

---

## Memory Architecture

### 🔹 Short-Term Memory (Context Retention)

```python
self.chat_history = []
```

- Stores ongoing conversation
- Used for:
  - pronoun resolution (“that account”)
  - remembering user details (name, intent)

Integrated using:

```python
MessagesPlaceholder(variable_name="chat_history")
```

---

### 🔹 Long-Term Memory (Adaptive Behavior)

Stored in:

```python
data/user_feedback.json
```

Example:

```json
{
  "tone_preference": "concise"
}
```

---

## Feedback Collection

The agent detects feedback signals from user input:

### Concise Mode Trigger

```text
"too long", "be brief", "extremely brief"
```

---

### Detailed Mode Trigger

```text
"explain more", "be detailed"
```

---

## Adaptation Logic

### Step 1: Detect Feedback

```python
if "too long" in query.lower():
```

---

### Step 2: Store Preference

```python
self._save_feedback("concise")
```

---

### Step 3: Update Behavior

```python
self.current_behavior = self._load_feedback_summary()
```

---

### Step 4: Inject into Prompt

```python
("system", f"Your current behavior mode: {self.current_behavior}")
```

---

## Behavioral Modes

| Mode     | Description                      |
| -------- | -------------------------------- |
| Default  | Balanced professional response   |
| Concise  | Short, direct, minimal output    |
| Detailed | Elaborate, explanatory responses |

---

## Prompt Design

The prompt dynamically adapts:

- Includes current behavior mode
- Includes chat history (context)
- Enforces safety rules

---

## Demonstration

### 🔹 Test 1: Short-Term Memory (Context Retention)

**Step A:**

> Hi, my name is Arun and I'm interested in Elite Savings.

**Step B:**

> What was the interest rate for that account?

**Behavior:**

- Agent remembers:
  - user name ("Arun")
  - referenced entity ("Elite Savings")

- Resolves “that account” correctly

---

### 🔹 Test 2: Long-Term Adaptive Memory

**Step A:**

> Your answers are too long. Be extremely brief.

**System Action:**

- Stores `"concise"` preference

---

**Step B:**

> Tell me about Starter Savings account.

**Behavior:**

- Response becomes **short and direct**
- Shows persistent behavior change

---

### 🔹 Test 3: Memory Boundary (Reset vs Persistence)

**Step A:**

> start over

**Behavior:**

- Clears short-term memory

---

**Step B:**

> Do you remember my name?

**Behavior:**

- Responds: No (short-term cleared)

---

**Step C:**

> Briefly explain mortgage

**Behavior:**

- Still concise
- Long-term preference persists

---

## Key Design Insight

The system separates memory into:

| Memory Type | Scope       | Persistence |
| ----------- | ----------- | ----------- |
| Short-Term  | Session     | Temporary   |
| Long-Term   | Preferences | Persistent  |

---

## Improvements Over Phase 6

| Feature                 | Phase 6 | Phase 7 |
| ----------------------- | ------- | ------- |
| Session memory          | ✅      | ✅      |
| Multi-step reasoning    | ✅      | ✅      |
| Feedback handling       | ❌      | ✅      |
| Adaptive behavior       | ❌      | ✅      |
| Personalization         | ❌      | ✅      |
| Memory boundary control | ❌      | ✅      |

---

## Benefits

- Personalized user experience
- Context-aware conversations
- Reduced repetition
- Persistent behavior adaptation
- Better conversational quality

---

## Limitations

- Feedback detection is rule-based
- No semantic understanding of feedback yet
- Long-term memory limited to tone only
- No database-backed persistence

---

## Summary

In this phase, the system evolves into an **adaptive conversational agent** by:

- Combining short-term and long-term memory
- Capturing and storing user feedback
- Dynamically adjusting response behavior
- Demonstrating clear before vs after improvements
- Implementing memory boundary control

This represents a significant step toward **real-world intelligent assistants** that can learn and adapt over time.

---

## Next Steps

Future enhancements may include:

- Semantic feedback classification (NLP-based)
- Multi-dimensional personalization
- Database-backed memory
- Reinforcement learning from user feedback
