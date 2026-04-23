import os
import json
import time
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_community.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger_utils import rag_log, ops_log

load_dotenv()

class LoanInput(BaseModel):
    principal: float = Field(..., description="Loan amount in dollars")
    annual_rate: float = Field(..., description="Interest rate in percentage")
    years: int = Field(..., description="Loan duration in years")

class EligibilityInput(BaseModel):
    credit_score: int = Field(..., description="Credit score between 300 and 850")
    monthly_income: float = Field(..., description="Monthly income in dollars")

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

class AdaptiveBankingAgent:

    def __init__(self, data_path="data/", prompt_version="v7.3"):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.feedback_file = "data/user_feedback.json"
        self.tools = [calculate_monthly_loan_payment, check_account_eligibility]
        self.chat_history = []

        self.data_path = data_path
        self.version = prompt_version
        self.prompt_file = "templates/prompt_registry.json"
        self.prompt_registry= self.load_prompt_registry()
        self.active_prompts = self.prompt_registry.get(
            self.version, 
            self.prompt_registry["v7.1"] # Fallback to v7.1 if version not found
        )
        
        # Load existing feedback to set initial behavior
        self.current_behavior = self._load_feedback_summary()

        loaders = {
            ".txt": TextLoader,
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
        }

        def create_loader(file_path):
            ext = os.path.splitext(file_path)[1]
            if ext in loaders:
                return loaders[ext](file_path)
            return None

        # Load all documents from the directory
        print(f"Loading documents from {data_path}...")
        docs = []
        if not os.path.exists(data_path):
            os.makedirs(data_path)

        for file in os.listdir(data_path):
            # Skip temporary Word files (~$) and hidden files (.)
            if file.startswith("~$") or file.startswith("."):
                print(f"Skipping temporary/hidden file: {file}")
                continue

            file_path = os.path.join(data_path, file)
            loader = create_loader(file_path)
            if loader:
                docs.extend(loader.load())

        # 2. Text Chunking (Mandatory Phase 4 Task)
        # Breaking long documents into smaller pieces for better retrieval
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)

        # Use a persistent directory to avoid tenant errors
        persist_directory = "./data/chroma_db"

        if os.path.exists(persist_directory):
            print("Loading existing vector database...")
            self.vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=OpenAIEmbeddings(),
                collection_name="banking_knowledge"
            )
        else:
            print("Creating new vector database...")
            self.vectorstore = Chroma.from_documents(
                documents=splits, 
                embedding=OpenAIEmbeddings(),
                collection_name="banking_knowledge",
                persist_directory=persist_directory
            )

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})

    def _load_feedback_summary(self):
        if os.path.exists(self.feedback_file):
            with open(self.feedback_file, "r") as f:
                data = json.load(f)
                # Logic: If user complained about verbosity, set 'concise' mode.
                if data.get("tone_preference") == "concise":
                    return "Be extremely brief and provide only numeric answers."
                elif data.get("tone_preference") == "detailed":
                    return "Be very conversational and explain the 'why' behind every bank policy."
        return "Be a professional and helpful banking assistant."

    def _save_feedback(self, preference):
        with open(self.feedback_file, "w") as f:
            json.dump({"tone_preference": preference}, f)
        # Update behavior immediately for the next interaction
        self.current_behavior = self._load_feedback_summary()

    def load_prompt_registry(self):
        if not os.path.exists(self.prompt_file):
            # Create a basic one if it doesn't exist to prevent crash
            return {"v7.1": {"system": "You are an assistant.", "rag": "{context}\n{question}"}}
        with open(self.prompt_file, "r") as f:
            return json.load(f)

    def get_prompt(self):
        system_msg = self.active_prompts["system"].format(
            version=self.version,
            behavior=self.current_behavior
        )
        return ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

    def ask(self, query):
        start_time = time.time()
        ops_log.info(f"[{self.version}] Process Request: {query[:30]}")

        # This helps us decide: Is this about banking or about the user?
        docs_with_scores = self.vectorstore.similarity_search_with_relevance_scores(query, k=3)

        relevant_docs = [doc for doc, score in docs_with_scores if score > 0.5]
        
        # 1. Handle Memory Reset
        if "start over" in query.lower():
            self.chat_history = []
            return "Session reset. How can I help you today?", 0
        
        # 2. RAG Retrieval
        docs = self.retriever.invoke(query)
        rag_log.info(f"[{self.version}]: {query}, Chunks Found: {len(docs)}")

        if len(docs) > 0:
            context_text = "\n\n".join([d.page_content for d in docs])
        else:
            context_text = "NONE: No bank documents match this query."

        rich_input = self.active_prompts["rag"].format(
            context=context_text,
            question=query
        )

        # 3. Memory Fix: Add the user's current query to history BEFORE invoking
        current_history = self.chat_history.copy()

        # 4. Execute
        agent = create_openai_tools_agent(self.llm, self.tools, self.get_prompt())
        executor = AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True,
            handle_parsing_errors=True
        )
        
        response = executor.invoke({
            "input": rich_input,
            "chat_history": current_history
        })
        
        # 5. Persistent Storage for NEXT turn
        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": response["output"]})

        latency = round(time.time() - start_time, 2)
        return response["output"], latency

if __name__ == "__main__":
    agent = AdaptiveBankingAgent()

    print("\n" + "="*50)
    print("TEST 1: SHORT-TERM MEMORY (Context Retention)")
    print("="*50)
    # Step A: Provide a fact
    print(f"User: Hi, my name is Arun and I'm interested in the Elite Savings account.")
    print(f"Agent: {agent.ask('Hi, my name is Arun and I\'m interested in the Elite Savings account.')}")
    
    # Step B: Test if it remembers the name and the account (Pronoun Resolution)
    print(f"\nUser: What was the interest rate for that account again?")
    print(f"Agent: {agent.ask('What was the interest rate for that account again?')}")

    print("\n" + "="*50)
    print("TEST 2: LONG-TERM ADAPTIVE MEMORY (Tone Change)")
    print("="*50)
    # Step A: Trigger a behavior change
    print(f"User: Your answers are too long. Please be extremely brief from now on.")
    print(f"Agent: {agent.ask('Your answers are too long. Please be extremely brief from now on.')}")
    
    # Step B: Verify the behavior persists for a new question
    print(f"\nUser: Tell me about the Starter Savings account.")
    print(f"Agent: {agent.ask('Tell me about the Starter Savings account.')}")
    # Logic: Response should be very short due to the JSON-stored preference.

    print("\n" + "="*50)
    print("TEST 3: MEMORY BOUNDARY (Reset vs. Persistence)")
    print("="*50)
    # Step A: Reset Short-term memory
    print(f"User: start over")
    print(f"Agent: {agent.ask('start over')}")
    
    # Step B: Verify Short-term is gone, but Long-term (Tone) remains
    print(f"\nUser: Do you remember my name?")
    print(f"Agent: {agent.ask('Do you remember my name?')}")
    # Logic: Should say "No" (Short-term reset).
    
    print(f"\nUser: Briefly explain what a mortgage is.")
    print(f"Agent: {agent.ask('Briefly explain what a mortgage is.')}")
    # Logic: Should still be concise because the JSON file wasn't deleted.