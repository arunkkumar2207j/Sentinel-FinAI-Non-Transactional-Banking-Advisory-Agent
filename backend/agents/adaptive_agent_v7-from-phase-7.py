import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import SystemMessage

load_dotenv()

class AdaptiveBankingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.feedback_file = "data/user_feedback.json"
        self.tools = [] # We'll focus on the prompt adaptation logic here
        self.chat_history = [] # Local short-term memory buffer
        
        # Load existing feedback to set initial behavior
        self.current_behavior = self._load_feedback_summary()

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

    def get_prompt(self):
        return ChatPromptTemplate.from_messages([
            ("system", f"Your current behavior mode: {self.current_behavior}\n"
                       "Safety: You are non-transactional. Refuse money transfers."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

    def ask(self, query):
        # Feedback Signal Detection
        if "too long" in query.lower() or "be brief" in query.lower():
            self._save_feedback("concise")
            return "Understood. I have updated my behavior to be more concise for our future interactions."
        
        if "explain more" in query.lower() or "be detailed" in query.lower():
            self._save_feedback("detailed")
            return "Understood. I will now provide more detailed explanations for you."

        # Execute normal reasoning
        agent = create_openai_tools_agent(self.llm, self.tools, self.get_prompt())
        executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        response = executor.invoke({
            "input": query,
            "chat_history": self.chat_history
            })
        
        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": response["output"]})

        return response["output"]

# --- PHASE 7 DEMONSTRATION ---

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
    # Logic: It should know "that account" refers to Elite Savings.

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