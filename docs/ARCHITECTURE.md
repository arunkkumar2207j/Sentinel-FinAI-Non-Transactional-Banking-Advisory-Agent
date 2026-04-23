# System Architecture: Sentinel-FinAI

**Version:** 1.0  
**Based on:** `main_for_streamlit.py` + `agents/adaptive_agent_v7.py`  
**Date:** 2026-04-23

---

## 📐 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI LAYER                        │
│  (main_for_streamlit.py)                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Chat Interface | Sidebar (Observability) | Session State   │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ uses
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT WRAPPER LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  SentinelProductionAgent                                      │
│  │  - Initializes AdaptiveBankingAgent                           │
│  │  - Handles errors gracefully                                  │
│  │  - Measures latency                                          │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ delegates
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CORE AGENT LAYER                               │
│  (agents/adaptive_agent_v7.py → AdaptiveBankingAgent)            │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  Components:                                                 │ │
│  │  • LLM: GPT-4o (temperature=0)                               │ │
│  │  • RAG: Chroma Vector DB + OpenAI Embeddings                 │ │
│  │  • Tools: Loan Calculator, Eligibility Checker               │ │
│  │  • Memory: Chat History (short-term) + JSON feedback (long) │ │
│  │  • Prompts: prompt_registry.json (v7.3)                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │ uses
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA & STORAGE LAYER                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  • data/ — Source documents (.txt, .pdf, .docx)             │ │
│  │  • data/chroma_db/ — Vector embeddings (persistent)          │ │
│  │  • data/user_feedback.json — Tone preference (adaptive)     │ │
│  │  • logs/ — Ops, RAG, Tools, Safety, Prompt logs             │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

### 1. **Presentation Layer** (`main_for_streamlit.py`)

**Purpose:** Web UI for user interaction.

**Key Elements:**

- `run_ui()` — Main Streamlit app function
- `st.session_state` — Persists `agent` and `messages` across reruns
- Sidebar — Observability (clear history button, log location)
- Chat input/output — Real-time messaging with latency display

**Flow:**

1. User types query → `st.session_state.agent.ask(prompt)`
2. Display response + latency
3. Log to `sentinel_ops.log`

---

### 2. **Agent Wrapper** (`SentinelProductionAgent` class)

**Purpose:** Production resilience layer (Phase 8 requirement).

**Responsibilities:**

- Initialize `AdaptiveBankingAgent` with error handling
- Wrap `ask()` with try/except for graceful degradation
- Measure and log latency
- Return user-friendly error messages on failure

**Note:** Currently a thin wrapper; can be extended for:

- Rate limiting
- Authentication
- Request validation
- Circuit breakers

---

### 3. **Core Agent** (`AdaptiveBankingAgent` class)

#### 3.1 Initialization (`__init__`)

```python
AdaptiveBankingAgent(data_path="data/", prompt_version="v7.3")
```

**Steps:**

1. Set up LLM: `ChatOpenAI(model="gpt-4o", temperature=0)`
2. Load tools list
3. Load prompt registry from `templates/prompt_registry.json`
4. Select active prompts based on `prompt_version`
5. Load user feedback from `data/user_feedback.json` → sets `current_behavior`
6. Document ingestion:
   - Scan `data_path` for `.txt`, `.pdf`, `.docx`
   - Skip temp files (`~$`) and hidden files (`.`)
   - Load with appropriate loader
7. Text chunking: `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)`
8. Vector DB:
   - If `data/chroma_db/` exists → load existing
   - Else → create new with `Chroma.from_documents()`
9. Create retriever: `vectorstore.as_retriever(search_kwargs={"k": 3})`

#### 3.2 Query Processing (`ask(query)`)

**Step-by-step:**

| Step | Action             | Details                                                                      |
| ---- | ------------------ | ---------------------------------------------------------------------------- |
| 1    | Log start          | `ops_log.info()`                                                             |
| 2    | Relevance scoring  | `similarity_search_with_relevance_scores(query, k=3)`                        |
| 3    | Memory reset check | If "start over" in query → clear `chat_history`                              |
| 4    | RAG retrieval      | `retriever.invoke(query)` → get top 3 chunks                                 |
| 5    | Context formatting | Join chunks or use "NONE" if empty                                           |
| 6    | Prompt building    | `rich_input = active_prompts["rag"].format(context, question)`               |
| 7    | Agent creation     | `create_openai_tools_agent(llm, tools, get_prompt())`                        |
| 8    | Execution          | `AgentExecutor.invoke({"input": rich_input, "chat_history": copy(history)})` |
| 9    | History update     | Append user query + assistant response to `chat_history`                     |
| 10   | Return             | `(response["output"], latency)`                                              |

**Important:** Chat history is copied before invocation to avoid mutation issues, then updated after.

#### 3.3 Memory System

**Short-term (ephemeral):**

- `self.chat_history` — List of `{role, content}` dicts
- Lives in memory only
- Cleared on "start over" or process restart

**Long-term (persistent):**

- `data/user_feedback.json` — Stores `{"tone_preference": "concise"|"detailed"}`
- Loaded on init → sets `current_behavior` string
- Updated via `_save_feedback(preference)`
- Persists across restarts

#### 3.4 Tools

**Tool 1: `calculate_monthly_loan_payment`**

- Inputs: `principal` (float), `annual_rate` (float), `years` (int)
- Formula: Standard amortization
- Output: String with monthly payment

**Tool 2: `check_account_eligibility`**

- Inputs: `credit_score` (int), `monthly_income` (float)
- Logic: `credit_score >= 680 AND monthly_income >= 5000` → eligible
- Output: Eligibility message

**Tool invocation:** Automatic via LangChain's `create_openai_tools_agent` — LLM decides when to call tools based on query.

#### 3.5 Prompt System

**Registry:** `templates/prompt_registry.json`

**Versions:**

- `v7.1` — Strict RAG (no general knowledge)
- `v7.2` — Hybrid (RAG priority, general knowledge fallback)
- `v7.3` (default) — Full hierarchy: chat_history → bank context → general knowledge + safety rule against investment advice

**Prompt structure:**

```
System message: formatted with {version} and {behavior}
Chat history: MessagesPlaceholder
Human message: {input}
Agent scratchpad: {agent_scratchpad} (for tool calls)
```

---

### 4. **Data Layer**

#### 4.1 Document Sources (`data/`)

- `bank_policies.txt` — General policies
- `Mortgage_Guidelines.docx` — Mortgage-specific rules
- `Savings_Policies.txt` — Savings product info
- `Security_and_Usage.pdf` — Security/usage policies
- `user_feedback.json` — Created on first feedback

#### 4.2 Vector Database (`data/chroma_db/`)

- **Format:** ChromaDB persistent storage
- **Embeddings:** OpenAI `text-embedding-ada-002` (via `OpenAIEmbeddings()`)
- **Collection name:** `banking_knowledge`
- **Rebuild:** Delete folder to force re-embedding

#### 4.3 Logging (`logs/`)

Five specialized loggers (from `utils/logger_utils.py`):
| Logger | File | Purpose |
|--------|------|---------|
| `ops_log` | `sentinel_ops.log` | Main operations (queries, latency, errors) |
| `rag_log` | `rag_retrieval.log` | Retrieved chunks, scores |
| `tool_log` | `tools_usage.log` | Tool calls and results |
| `safety_log` | `safety_and_tone.log` | Safety checks, tone adjustments |
| `prompt_log` | `prompt_history.log` | Prompt versions used |

---

## 🔄 Data Flow Diagram

```
User Query (Streamlit)
        ↓
SentinelProductionAgent.process_request()
        ↓
AdaptiveBankingAgent.ask(query)
        ↓
① RAG Retrieval (Chroma DB) → context_text
        ↓
② Prompt Assembly (system + history + rich_input)
        ↓
③ LLM + Tools (GPT-4o + loan/eligibility tools)
        ↓
④ Response + Latency
        ↓
Update chat_history
        ↓
Return to UI → Display + Log
```

---

## 🛡️ Safety & Constraints

1. **Non-Transactional:** Agent cannot perform money movements (by design — no transaction tools)
2. **Investment Advice Block:** v7.3 prompt explicitly refuses investment advice
3. **Temperature=0:** Deterministic outputs, low hallucination risk
4. **RAG Grounding:** Context from bank documents is primary source
5. **Error Handling:** Wrapper catches exceptions, returns friendly message
6. **Input Validation:** Tools have Pydantic schemas + manual checks

---

## 🔧 Configuration Points

| File                             | Setting                                  | Purpose                  |
| -------------------------------- | ---------------------------------------- | ------------------------ |
| `templates/prompt_registry.json` | `prompt_version` (default: "v7.3")       | Switch prompt behavior   |
| `data/user_feedback.json`        | `tone_preference` ("concise"/"detailed") | Adaptive tone            |
| `adaptive_agent_v7.py`           | `chunk_size=1000`, `chunk_overlap=100`   | RAG chunking             |
| `adaptive_agent_v7.py`           | `retriever k=3`                          | Number of context chunks |
| `main_for_streamlit.py`          | Logging level `INFO`                     | Verbosity                |

---

## 📦 Dependencies

**UI:** `streamlit`  
**LLM:** `langchain-openai`, `openai`  
**Vector DB:** `langchain-chroma`, `chromadb`  
**Document loaders:** `langchain-community`, `pypdf`, `docx2txt`  
**Orchestration:** `langchain`, `langchain-core`, `langchain-agents`  
**Validation:** `pydantic`  
**Config:** `python-dotenv`  
**Utilities:** `langchain-text-splitters`

See `backend/requirements.txt` for exact versions.

---

## 🚀 Execution Modes

### Mode 1: Streamlit UI (Normal)

```bash
cd backend
streamlit run main_for_streamlit.py
```

→ Opens browser, interactive chat

### Mode 2: Direct Agent Test (Standalone)

```bash
python backend/agents/adaptive_agent_v7.py
```

→ Runs built-in test suite (memory, tone adaptation, reset)

### Mode 3: Evaluation Script

```bash
python backend/evaluator.py
```

→ Runs 5 test scenarios, saves results to `logs/evaluation_results.json`

---

## 🎯 Key Design Decisions

| Decision                    | Rationale                                                   |
| --------------------------- | ----------------------------------------------------------- |
| **GPT-4o**                  | State-of-the-art reasoning, tool calling, low hallucination |
| **ChromaDB**                | Lightweight, persistent, no external server needed          |
| **LangChain AgentExecutor** | Built-in tool orchestration, error handling                 |
| **Streamlit**               | Fast UI prototyping, session state built-in                 |
| **Temperature=0**           | Deterministic, reproducible responses for banking           |
| **3-chunk retrieval**       | Balance context richness vs. noise/truncation               |
| **JSON feedback file**      | Simple persistent memory without database                   |
| **Prompt registry**         | A/B test different prompting strategies                     |
| **Wrapper class**           | Separation of concerns — UI vs. business logic              |

---

## 📊 Observability

**Logs location:** `backend/logs/`

**What to monitor:**

- `sentinel_ops.log` — Query volume, latency, errors
- `rag_retrieval.log` — Whether documents are being found (chunks count)
- `tools_usage.log` — Tool call frequency (indicates complex queries)
- `safety_and_tone.log` — Safety rule triggers, tone switches
- `prompt_history.log` — Which prompt version is active

**Metrics:**

- Latency (seconds) — logged per query
- Retrieval scores — relevance filtering (>0.5 threshold used in code)
- Tool success/failure — from AgentExecutor output

---

## 🔄 Future Extension Points

1. **Add new tools:** Extend `self.tools` list in `__init__`
2. **Add memory:** Implement `ConversationBufferMemory` or external DB
3. **Multi-turn planning:** Add `PlanExecutor` or `ReAct` pattern
4. **Human-in-the-loop:** Add " escalate to human" tool
5. **Audit trail:** Store all interactions in database
6. **Rate limiting:** Add to `SentinelProductionAgent` wrapper
7. **Caching:** Add Redis cache for frequent queries
8. **A/B testing:** Route users to different `prompt_version` values

---

**End of Architecture Document**
