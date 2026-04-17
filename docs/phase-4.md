# Phase 4: Add Knowledge & Retrieval

## Overview

**Coding:** Required
**Tools/Skills:** Embeddings, Semantic Search, RAG (Retrieval-Augmented Generation), Text Chunking, Vector Stores (Chroma), Retrieval Evaluation

In this phase, the agent is enhanced with **knowledge retrieval capabilities** using embeddings and semantic search. Unlike Phase 3, which relied only on LLM reasoning, this phase grounds responses in **actual documents**, improving accuracy and reliability.

---

## Objective

- Implement embeddings and semantic retrieval
- Enable document-based responses
- Improve accuracy over LLM-only responses
- Handle missing knowledge scenarios
- Support multiple document formats

---

## Implementation

This phase is implemented in **two stages**:

---

## 🔹 Version 1: Single-Source RAG (`knowledge_v3_1.py`)

### Approach

- Load a single text file:
  `bank_policies.txt`
- Split content using simple newline-based chunking
- Convert chunks into embeddings
- Store embeddings in **Chroma vector database**
- Retrieve top relevant chunks for each query

---

### Workflow

1. Load text file
2. Create chunks
3. Generate embeddings using `OpenAIEmbeddings`
4. Store in Chroma
5. Retrieve relevant chunks
6. Pass context to LLM

---

### Example Queries

- “What is the rate for Elite Savings?”
- “What is the interest rate for a Gold Credit Card?” _(missing data case)_
- “Transfer $1000 to my savings” _(safety case)_

---

### Observations

- Accurate answers when data exists
- Correctly avoids hallucination when data is missing
- Maintains safety constraints from Phase 3

---

## 🔹 Version 2: Multi-Source RAG (`knowledge_v3_2.py`)

### Approach

Extended RAG system to support **multiple document formats**:

| File Type | Example                  |
| --------- | ------------------------ |
| `.txt`    | Savings_Policies.txt     |
| `.docx`   | Mortgage_Guidelines.docx |
| `.pdf`    | Security_and_Usage.pdf   |

---

### Document Loading

Used multiple loaders:

- `TextLoader` → `.txt`
- `Docx2txtLoader` → `.docx`
- `PyPDFLoader` → `.pdf`

---

### Text Chunking

Used:

```python
RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
```

Benefits:

- Better semantic grouping
- Improved retrieval accuracy

---

### Retrieval Pipeline

1. Load all documents from `/data` folder
2. Convert documents into chunks
3. Generate embeddings
4. Store in Chroma
5. Retrieve top 3 relevant chunks
6. Inject context into prompt
7. Generate grounded response

---

## RAG Prompt Design

The agent uses a structured prompt:

- Context-driven answering
- Strict safety rules
- No hallucination allowed

---

## Example Evaluation

### Query 1 (TXT Source)

**Q:** What is the APY for the Elite Savings account?
**Result:** Correctly retrieved from `Savings_Policies.txt`

---

### Query 2 (DOCX Source)

**Q:** What documents are needed for a 30-year mortgage?
**Result:** Retrieved from `Mortgage_Guidelines.docx`

---

### Query 3 (PDF Source)

**Q:** Can you increase my ATM limit?
**Result:** Responded using `Security_and_Usage.pdf` policies

---

### Query 4 (Missing Data)

**Q:** Gold Credit Card interest rate
**Result:**

> “I don't have that information in my current records.”

✅ No hallucination

---

### Query 5 (Safety Test)

**Q:** Transfer $1000
**Result:**

> Refused due to NON-TRANSACTIONAL rule

---

## Improvements Over Phase 3

| Aspect               | Phase 3 (LLM Only) | Phase 4 (RAG) |
| -------------------- | ------------------ | ------------- |
| Accuracy             | Medium             | High          |
| Hallucination        | High               | Low           |
| Explainability       | Low                | High          |
| Data grounding       | ❌                 | ✅            |
| Multi-source support | ❌                 | ✅            |

---

## Limitations

- Retrieval quality depends on document quality
- No ranking optimization (basic similarity search)
- No persistent vector DB (recreated each run)
- Context size limited by LLM

---

## Handling Missing Information

System explicitly handles missing data:

- If no relevant chunks → returns fallback message
- Avoids guessing or hallucination

---

## Summary

In this phase, the agent was enhanced by:

- Implementing embeddings and semantic search
- Building a RAG pipeline using Chroma
- Supporting multiple document formats
- Improving accuracy and reliability
- Maintaining strict safety constraints

This phase represents a major step toward a **production-ready AI advisory system**.

---

## Next Steps

Phase 5 will focus on:

- Tool integration
- External API usage
- Structured decision-making
