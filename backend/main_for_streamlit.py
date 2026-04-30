import os
import time
import logging
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from agents.adaptive_agent_v7 import AdaptiveBankingAgent

load_dotenv()
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/sentinel_ops.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@st.cache_resource
def get_agent():
    """Load ChromDB + LLM exactly once, shared across all sessions."""
    return AdaptiveBankingAgent()

class SentinelProductionAgent:
    def __init__(self, agent: AdaptiveBankingAgent):
        self.agent = agent
        logger.info("Sentinel-FinAI Agent initialized successfully.")
        # try:
        #     self.agent = AdaptiveBankingAgent()
        #     logger.info("Sentinel-FinAI Agent initialized successfully.")
        # except Exception as e:
        #     logger.error(f"Initialization Failed: {str(e)}")
        #     st.error("Critical System Failure: Could not load AI Model.")

    def process_request(self, query):
        start_time = time.time()
        try:
            if not query.strip():
                return "System: Input query cannot be empty.", 0
            
            response = self.agent.ask(query)
            response_text = response[0] if isinstance(response, tuple) else response
            
            latency = round(time.time() - start_time, 2)
            logger.info(f"Query: {query[:30]}... | Latency: {latency}s | Status: SUCCESS")
            return response_text, latency

        except Exception as e:
            logging.error(f"Error: {str(e)}")
            # Graceful failure handling (Phase 8 requirement)
            latency = round(time.time() - start_time, 2)
            return "I'm sorry, I encountered a technical glitch while processing your request. Please try again."


def run_ui():
    st.set_page_config(page_title="Sentinel-FinAI", page_icon="🏦")
    st.title("🏦 Sentinel-FinAI")
    st.caption("Lead-Level Banking Advisory Agent (Phase 8 Deployment)")

    agent = get_agent()

    # Ensure the agent instance persists to keep chat_history alive
    # if "agent" not in st.session_state:
    #     st.session_state.agent = AdaptiveBankingAgent()

    # Session State Management
    if "production_agent" not in st.session_state:
        st.session_state.production_agent = SentinelProductionAgent(agent)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("System Observability")
        if st.button("Clear History"):
            st.session_state.messages = []
            # st.session_state.agent.chat_history = [] 
            agent.chat_history = []
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
            response_text, latency = st.session_state.production_agent.process_request(prompt)
            st.markdown(response_text)
            st.caption(f"Latency: {latency}s")
            
        st.session_state.messages.append({"role": "assistant", "content": response_text})

if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    run_ui() 