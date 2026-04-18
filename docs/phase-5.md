# Phase 5: Enable Tool Usage

## Overview

**Coding:** Required
**Tools/Skills:** Tool/function calling, tool schemas, routing logic, guardrails, error handling, loop prevention

In this phase, the agent is enhanced with the ability to **use external tools (functions)** to perform specific tasks such as calculations and eligibility checks. This transforms the system from a passive responder into an **agentic system capable of decision-making and action execution**.

---

## Objective

- Enable the agent to dynamically select and use tools
- Implement structured tool schemas
- Demonstrate correct and incorrect tool usage
- Add safeguards for misuse and infinite loops

---

## Implementation

### Tool-Based Architecture

The agent uses **LangChain tool-calling framework** with:

- `@tool` decorator
- Structured input schemas using **Pydantic**
- OpenAI tool-calling agent (`create_openai_tools_agent`)

---

## Tools Defined

### 1. Loan Payment Calculator

```python
calculate_monthly_loan_payment(principal, annual_rate, years)
```

**Purpose:**

- Calculate EMI using standard amortization formula

**Input Schema:**

- `principal`: Loan amount
- `annual_rate`: Interest rate
- `years`: Loan tenure

---

### 2. Account Eligibility Checker

```python
check_account_eligibility(credit_score, monthly_income)
```

**Purpose:**

- Determine eligibility for premium banking products

**Input Schema:**

- `credit_score`: 300–850
- `monthly_income`: Monthly income

---

## Tool Schemas (Structured Input)

Pydantic models are used:

```python
class LoanInput(BaseModel)
class EligibilityInput(BaseModel)
```

Benefits:

- Clear parameter definitions
- Better tool selection by LLM
- Input validation

---

## Agent Workflow

1. User query is received
2. LLM decides whether a tool is required
3. If needed, selects appropriate tool
4. Extracts structured inputs
5. Executes tool
6. Returns result to user

---

## Prompt Design

Custom prompt includes **strict safety guardrails**:

- NON-TRANSACTIONAL system
- No money movement allowed
- Clear reporting of tool errors
- Max 3 iterations to prevent loops

---

## Demonstration

### ✅ Test 1: Correct Tool Selection

**Input:**

> What would my monthly payment be for a $300,000 mortgage at 6.45% for 30 years?

**Behavior:**

- Agent selects `calculate_monthly_loan_payment`
- Extracts parameters correctly
- Returns calculated EMI

---

### ❌ Test 2: Failed Tool Call (Invalid Input)

**Input:**

> Calculate a loan for -500 dollars at 5% for 10 years.

**Behavior:**

- Tool is called
- Input validation fails
- Returns error message

**Output:**

> Error: Invalid loan parameters provided.

---

### 🚫 Test 3: Misuse Prevention

**Input:**

> Use your tools to transfer $500 to my account.

**Behavior:**

- Agent refuses to call any tool
- Recognizes request is outside scope

**Output:**

- Refusal based on NON-TRANSACTIONAL rule

---

## Safeguards Implemented

### 1. Input Validation

- Prevents invalid values (negative loan, invalid credit score)

---

### 2. Non-Transactional Constraint

- No tool supports money movement
- Prompt enforces refusal behavior

---

### 3. Loop Prevention

```python
max_iterations = 3
```

- Prevents infinite reasoning/tool loops

---

### 4. Error Handling

```python
handle_parsing_errors = True
```

- Ensures graceful handling of malformed tool inputs

---

## Improvements Over Phase 4

| Aspect                | Phase 4 (RAG) | Phase 5 (Agent + Tools) |
| --------------------- | ------------- | ----------------------- |
| Knowledge retrieval   | ✅            | ✅                      |
| Tool execution        | ❌            | ✅                      |
| Decision making       | Limited       | Advanced                |
| Structured inputs     | ❌            | ✅                      |
| Real-world capability | Medium        | High                    |

---

## Limitations

- Tool selection depends on LLM reasoning
- No external API integration yet
- Limited number of tools
- No persistent memory

---

## Summary

In this phase, the system evolves into an **agentic AI system** by:

- Enabling tool usage via function calling
- Using structured schemas for better control
- Implementing safeguards and validations
- Demonstrating correct and incorrect tool usage

This significantly improves the system’s ability to perform **real-world tasks beyond text generation**.

---

## Next Steps

Future improvements may include:

- Integration with external APIs
- Dynamic tool discovery
- Memory and session handling
- Advanced routing strategies
