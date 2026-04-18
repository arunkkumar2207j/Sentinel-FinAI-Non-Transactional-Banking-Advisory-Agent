import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

class LoanInput(BaseModel):
    principal: float = Field(..., description="Loan amount in dollars")
    annual_rate: float = Field(..., description="Interest rate in percentage")
    years: int = Field(..., description="Loan duration in years")

class EligibilityInput(BaseModel):
    credit_score: int = Field(..., description="Credit score between 300 and 850")
    monthly_income: float = Field(..., description="Monthly income in dollars")

# --- STEP 1: DEFINE TOOLS (Task: Define at least two tools) ---

@tool(args_schema=LoanInput)
def calculate_monthly_loan_payment(principal: float, annual_rate: float, years: int) -> str:
    """
    Calculates the monthly payment for a loan based on principal, rate, and tenure.
    Use this for mortgage or personal loan inquiries.
    """
    # Safeguard: Basic input validation
    if principal <= 0 or annual_rate < 0 or years <= 0:
        return "Error: Invalid loan parameters provided."
        
    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12
    
    # Standard Amortization Formula: P [ i(1 + i)^n ] / [ (1 + i)^n – 1]
    payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return f"The estimated monthly payment is ${payment:.2f} over {years} years at {annual_rate}%."

@tool(args_schema=EligibilityInput)
def check_account_eligibility(credit_score: int, monthly_income: float) -> str:
    """
    Checks if a user is eligible for an 'Elite Savings' or 'Premium Loan' product.
    """
    # Safeguard: Against unrealistic inputs
    if credit_score > 850 or credit_score < 300:
        return "Error: Credit score must be between 300 and 850."

    if credit_score >= 680 and monthly_income >= 5000:
        return "Eligible for Elite products. Please contact a branch for final approval."
    else:
        return "Does not meet the current automated criteria for Elite products."

# --- STEP 2: IMPLEMENT AGENT LOGIC ---

class SentinelAgenticAssistant:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = [calculate_monthly_loan_payment, check_account_eligibility]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a banking advisory agent.

            SAFETY GUARDRAILS:
            - NON-TRANSACTIONAL: never move money
            - Report tool errors clearly
            - Only provide estimates
            - Max 3 tool iterations
            """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True, 
            max_iterations=3, # Loop prevention
            handle_parsing_errors=True
        )

    def run(self, user_input):
        return self.agent_executor.invoke({"input": user_input})["output"]

# --- STEP 3: DEMONSTRATION (Tasks: Correct selection vs Incorrect/Failure) ---

if __name__ == "__main__":
    assistant = SentinelAgenticAssistant()

    print("\n--- TEST 1: Correct Tool Selection ---")
    print(assistant.run("What would my monthly payment be for a $300,000 mortgage at 6.45% for 30 years?"))

    print("\n--- TEST 2: Incorrect/Failed Call (Guardrail Trigger) ---")
    # This will trigger the 'invalid parameters' check in the tool
    print(assistant.run("Calculate a loan for -500 dollars at 5% for 10 years."))

    print("\n--- TEST 3: Misuse Prevention (Non-Transactional) ---")
    # LLM should refuse to use a calculator for a 'transfer' because it doesn't match the tool schema
    print(assistant.run("Use your tools to transfer $500 to my account."))