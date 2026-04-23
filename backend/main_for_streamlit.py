import os
import time
import logging
import json
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from agents.adaptive_agent_v7 import AdaptiveBankingAgent

load_dotenv()
os.makedirs("logs", exist_ok=True)

# --- TASK: Add Logging and Tracing ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/sentinel_ops.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SentinelProductionAgent:
    def __init__(self):
        # In a real deployment, we'd initialize the full agent here
        # For now, we simulate the wrapper for Phase 8 resilience
        try:
            self.agent = AdaptiveBankingAgent()
            logger.info("Sentinel-FinAI Agent initialized successfully.")
        except Exception as e:
            logger.error(f"Initialization Failed: {str(e)}")
            st.error("Critical System Failure: Could not load AI Model.")

    def process_request(self, query):
        start_time = time.time()
        try:
            # TASK: Handle Runtime Failures Gracefully
            if not query.strip():
                return "System: Input query cannot be empty.", 0
            
            # Simulate agent call (Replace with self.agent.ask(query))
            response = self.agent.ask(query)
            
            latency = round(time.time() - start_time, 2)
            logger.info(f"Query: {query[:30]}... | Latency: {latency}s | Status: SUCCESS")
            return response, latency

        except Exception as e:
            latency = round(time.time() - start_time, 2)
            logging.error(f"Error: {str(e)}")
            # Graceful failure handling (Phase 8 requirement)
            return "I'm sorry, I encountered a technical glitch while processing your request. Please try again.", latency

# --- TASK: Deploy Locally (Streamlit UI) ---
def run_ui():
    st.set_page_config(page_title="Sentinel-FinAI", page_icon="🏦")
    st.title("🏦 Sentinel-FinAI")
    st.caption("Lead-Level Banking Advisory Agent (Phase 8 Deployment)")

    # Ensure the agent instance persists to keep chat_history alive
    if "agent" not in st.session_state:
        st.session_state.agent = AdaptiveBankingAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("System Observability")
        if st.button("Clear History"):
            st.session_state.messages = []
            st.session_state.agent.chat_history = [] 
            st.rerun()
        st.divider()
        st.info("Logs: `logs/sentinel_ops.log`")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("How can I help you today?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Call the persistent agent and capture performance metrics
            response_text, latency = st.session_state.agent.ask(prompt)
            
            st.markdown(response_text)
            st.caption(f"Latency: {latency}s")
            
            # Log the transaction for Phase 8 observability
            logger.info(f"Query: {prompt[:30]} | Latency: {latency}s | Status: SUCCESS")
            
        st.session_state.messages.append({"role": "assistant", "content": response_text})

if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    run_ui() 