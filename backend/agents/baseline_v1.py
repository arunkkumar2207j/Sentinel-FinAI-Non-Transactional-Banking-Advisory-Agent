import logging

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  handlers=[logging.FileHandler('baseline_interactions.log'), logging.StreamHandler()]
)

class BaselineBankingAgent:
  def __init__(self):
    # Basic knowledge stored in a rigid dictionary (rules/templates)
    self.knowledge_base = {
      "who are you":"I am an AI assistant designed to provide basic banking information.",
      "interest rates":"Out current interest rate is 3.5% APY.",
      "fixed deposit":"We offer fixed deposit with tenure ranging from 7 days to 10 years.",
      "mortgage":"Home loan interest rates starts at 6.5% for eligible customers.",
      "opening account":"To open an account, you need valid ID proof, proof of address, and a minimum deposit of $100."
    }
  def process_request(self, user_input):
    logging.info(f"User Input: {user_input}")
    query = user_input.strip().lower()

    if not query:
      response = "I didn't receive any input. How can I help?"

    # Demonstrate safety limitations 
    # In this baseline, we use simple keyword matching which is unsafe for banking.
    if "transfer" in query or "send money" in query:
      response = "I see you need to move money. Please provide the account number and amount to transfer."
      logging.warning(f"SAFETY FAILURE: Agent attempts to facilitate a transaction.")
      return response

    # Basic response generation logic
    for key in self.knowledge_base:
      if key in query:
        response = self.knowledge_base[key]
        logging.info(f"Response Generated: {response}")
        return response
    
    # Default fallback for unknown queries
    response = "I'm sorry, I don't have information on that topic."
    logging.info(f"Fallback Response: {response}")
    return response
  
if __name__ == "__main__":
  agent = BaselineBankingAgent()
  print("--- Sentinel FinAI Baseline Agent (Phase 2) ---")
  print("Ask me about interest rates, mortgages, or accounts. Type 'exit' to stop.")

  while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
      break
    response = agent.process_request(user_input)
    print(f"Agent: {response}")