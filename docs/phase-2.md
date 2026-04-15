# Phase 2: Build a Basic Working Agent

## Overview

**Coding:** Required
**Tools/Skills:** Python, CLI workflow, input/output handling, basic rules/templates, logging

In this phase, a baseline AI agent was implemented using a simple rule-based approach. The goal is to establish a working system and highlight its limitations before introducing more advanced capabilities.

---

## Objective

- Create a Python-based agent
- Handle user input and generate responses
- Demonstrate baseline limitations
- Log interactions for analysis

---

## Implementation

### Approach

A simple rule-based agent was built using:

- A predefined dictionary as a knowledge base
- Keyword matching for query understanding
- Basic logging for tracking interactions

The agent runs in a CLI loop and responds to user queries.

---

### Key Components

#### 1. Knowledge Base

A static dictionary is used to store predefined responses:

- Interest rates
- Fixed deposits
- Mortgage information
- Account opening requirements

This represents a **template-based response system**.

---

#### 2. Input Handling

- User input is taken via CLI
- Input is normalized (trimmed and converted to lowercase)
- Empty inputs are handled with a fallback response

---

#### 3. Response Generation

- Keyword matching is used to identify intent
- If a keyword matches → predefined response is returned
- If no match → fallback response is returned

---

#### 4. Logging

All interactions are logged using Python’s logging module:

- User input
- Generated response
- Safety warnings

Logs are stored in:

```bash
baseline_interactions.log
```

---

## Sample Interactions

**Example 1: Known Query**

```
You: What is the interest rate?
Agent: Our current interest rate is 3.5% APY.
```

**Example 2: Unknown Query**

```
You: What are tax implications?
Agent: I'm sorry, I don't have information on that topic.
```

**Example 3: Unsafe Request (Failure Case)**

```
You: Transfer $500 to my account
Agent: I see you need to move money. Please provide the account number and amount to transfer.
```

⚠️ This demonstrates a **safety failure**.

---

## Baseline Limitations

### 1. Rigid Keyword Matching

- The system only works if exact keywords are present
- Slight variations in phrasing may fail

**Example:**

- “interest rates” → works
- “rate of interest” → may fail

---

### 2. No Context Understanding

- The agent cannot understand intent beyond keywords
- No semantic reasoning

---

### 3. Safety Failure (Critical)

- The agent incorrectly attempts to assist with financial transactions
- Violates **non-transactional requirement**

This is logged as:

```
SAFETY FAILURE: Agent attempts to facilitate a transaction.
```

---

### 4. No Learning or Adaptation

- Responses are static
- No improvement over time

---

### 5. Limited Knowledge Scope

- Only predefined topics are supported
- Cannot handle real-world complexity

---

## Why This Is Insufficient for Real Users

This baseline agent is not suitable for production because:

- It cannot handle natural language variations
- It lacks reasoning and contextual understanding
- It fails critical safety requirements (e.g., transaction handling)
- It cannot scale beyond a small predefined knowledge base

In real-world banking scenarios, users expect:

- Accurate and context-aware responses
- Safe handling of sensitive requests
- Ability to understand complex queries

This baseline highlights the need for:

- LLM integration
- Retrieval-based knowledge systems
- Strong safety guardrails

---

## Summary

In this phase, a basic working agent was successfully implemented to:

- Accept user input
- Generate rule-based responses
- Log interactions
- Demonstrate clear limitations

This serves as the foundation for the next phase, where the agent will be enhanced using LLM capabilities to improve flexibility, intelligence, and safety.
