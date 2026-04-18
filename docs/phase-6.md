# Phase 6: Planning, Memory & Context

## Overview

**Coding:** Required
**Tools/Skills:** Multi-step reasoning, task decomposition, conversation memory, session handling, context retention, memory reset

In this phase, the agent is enhanced with **stateful memory and planning capabilities**, enabling it to handle **multi-turn conversations** and perform **context-aware reasoning**. Unlike previous phases, the agent can now remember user inputs and reuse them intelligently across interactions.

---

## Objective

- Introduce multi-step reasoning and planning
- Add conversation memory (short-term session memory)
- Improve multi-turn interaction quality
- Implement memory retention and reset behavior

---

## Implementation

The system is extended into a **stateful agent** using:

- `RunnableWithMessageHistory` for memory integration
- `ChatMessageHistory` for session-based storage
- Custom prompt instructions for planning and memory usage

---

## Memory Architecture

### Session-Based Memory

- Each user is assigned a `session_id`
- Conversation history is stored in a dictionary:

```python id="q9h2vk"
self.memory_store = {}
```

- Each session maintains its own conversation context

---

### Memory Retrieval

```python id="v6q4am"
def get_session_history(self, session_id: str):
```

- Retrieves or initializes chat history
- Enables persistent conversation across multiple queries

---

### Memory Integration

```python id="z9o0tr"
RunnableWithMessageHistory(...)
```

- Injects previous conversation into prompt
- Allows agent to “remember” prior inputs

---

## Planning & Reasoning

### Prompt Design

The system prompt includes explicit planning instructions:

- Break complex queries into steps
- Use previously provided information
- Avoid re-asking known details

---

### Example Planning Behavior

For a complex query:

> “Am I eligible and what’s my loan interest?”

Agent performs:

1. Retrieve user’s previous data (age, credit score)
2. Call eligibility tool
3. Call loan calculation tool
4. Combine results

---

## Tools Used

Reused from Phase 5 with structured schemas:

- `calculate_loan_interest`
- `check_policy_eligibility`

---

## Memory Retention Rules

- Memory persists within a session
- Previous user inputs are reused
- Context is automatically injected into each query

---

## Memory Reset Behavior

```python id="3dxw7m"
if "start over" in query.lower() or "new session" in query.lower():
```

- Clears stored conversation history
- Starts fresh interaction

---

## Demonstration

### Step 1: Provide Context

**Input:**

> Hi, I'm 30 years old and my credit score is 750.

**Behavior:**

- Stores user information in memory

---

### Step 2: Multi-step Reasoning + Memory

**Input:**

> Am I eligible for Elite account? Also calculate interest.

**Behavior:**

- Retrieves stored age and credit score
- Calls eligibility tool
- Calls loan calculation tool
- Combines both outputs

---

### Step 3: Memory Reset

**Input:**

> Let's start over

**Behavior:**

- Clears session memory
- Starts new conversation

---

## Improvements Over Phase 5

| Feature                  | Phase 5 (Agent + Tools) | Phase 6 (Stateful Agent) |
| ------------------------ | ----------------------- | ------------------------ |
| Tool usage               | ✅                      | ✅                       |
| Multi-step reasoning     | Limited                 | Advanced                 |
| Memory                   | ❌                      | ✅                       |
| Context awareness        | ❌                      | ✅                       |
| Multi-turn conversations | Basic                   | Strong                   |

---

## Benefits

- More natural conversations
- Reduced repetition
- Better user experience
- Context-aware decision making

---

## Limitations

- Memory is session-based (not persistent across restarts)
- No long-term storage (e.g., database)
- Depends on LLM reasoning for planning accuracy

---

## Summary

In this phase, the system evolves into a **stateful conversational agent** by:

- Adding session-based memory
- Enabling multi-step reasoning and planning
- Supporting multi-turn conversations
- Implementing memory reset mechanisms

This significantly enhances the system’s ability to simulate **real-world conversational assistants**.

---

## Next Steps

Future improvements may include:

- Persistent memory using databases
- User profiling and personalization
- Advanced planning strategies
- Integration with external systems
