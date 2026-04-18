import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import tool
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

class LoanInput(BaseModel):
    principal: float = Field(..., description="Loan amount in dollars")
    annual_rate: float = Field(..., description="Interest rate in percentage")
    years: int = Field(..., description="Loan duration in years")

class EligibilityInput(BaseModel):
    credit_score: int = Field(..., description="Credit score between 300 and 850")
    age: int = Field(..., description="User's age in years")

# --- TOOLS (From Phase 5) ---

@tool(args_schema=LoanInput)
def calculate_loan_interest(principal: float, annual_rate: float, years: int) -> str:
    """Calculates total interest over the life of a loan."""
    if principal <= 0 or annual_rate < 0 or years <= 0:
        return "Error: Invalid loan parameters."
    total_interest = principal * (annual_rate / 100) * years
    return f"The total interest is ${total_interest:,.2f}."

@tool(args_schema=EligibilityInput)
def check_policy_eligibility(credit_score: int, age: int) -> str:
    """Checks if a user meets Elite account requirements."""
    if credit_score >= 720 and age >= 18:
        return "Eligible for Elite products."
    return "Not currently eligible for Elite products."

# --- PHASE 6: MEMORY & PLANNING LOGIC ---

class SentinelStatefulAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = [calculate_loan_interest, check_policy_eligibility]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You have MEMORY. Reference previous parts of the conversation.

            PLANNING RULES:
            - If a user asks a complex question, break it into steps.
            - Always check memory for previously provided details (like credit score or age) 
        #    before asking the user again.
            - MEMORY RESET: If the user says 'start over' or 'new session', ignore previous context.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        # 2. Agent Core
        agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, # Visible reasoning/planning
            max_iterations=5
        )

        # 3. Memory Store: Dictionary to hold histories by session_id
        self.memory_store = {}

    def get_session_history(self, session_id: str):
        if session_id not in self.memory_store:
            self.memory_store[session_id] = ChatMessageHistory()
        return self.memory_store[session_id]

    def ask(self, query, session_id="default_user"):
        # Wrap the executor with message history handling
        agent_with_chat_history = RunnableWithMessageHistory(
            self.agent_executor,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        # Handle Memory Reset Task
        if "start over" in query.lower() or "new session" in query.lower():
            self.memory_store[session_id] = ChatMessageHistory()
            return "Session has been reset. How can I help you today?"

        response = agent_with_chat_history.invoke(
            {"input": query},
            config={"configurable": {"session_id": session_id}}
        )
        return response["output"]

# --- PHASE 6 DEMONSTRATION ---

if __name__ == "__main__":
    agent = SentinelStatefulAgent()
    sid = "user_123"

    print("\n[STEP 1: Providing Context]")
    print(agent.ask("Hi, I'm 30 years old and my credit score is 750.", session_id=sid))

    print("\n[STEP 2: Multi-step Reasoning + Memory]")
    # The agent should remember age/score and calculate the loan automatically
    print(agent.ask("Based on my profile, am I eligible for an Elite account? Also, what's the interest on a $10k loan at 5% for 2 years?", session_id=sid))

    print("\n[STEP 3: Memory Reset]")
    print(agent.ask("Actually, let's start over.", session_id=sid))