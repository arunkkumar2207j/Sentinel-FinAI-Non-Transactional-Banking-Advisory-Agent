import logging
import os

os.makedirs("logs", exist_ok=True)

def setup_custom_logger(name, log_file, level=logging.INFO):
  """Function to setup as many loggers as you want"""
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

  handler = logging.FileHandler(f"logs/{log_file}")
  handler.setFormatter(formatter)

  logger = logging.getLogger(name)
  logger.setLevel(level)

  # Prevent duplicate logs if the logger is re-initialized
  if not logger.handlers:
    logger.addHandler(handler)

  return logger


# Initialize specialized loggers
memory_log = setup_custom_logger("memory", "memory_trace.log")
rag_log = setup_custom_logger("rag", "rag_retrieval.log")
tool_log = setup_custom_logger("tools", "tools_usage.log")
safety_log = setup_custom_logger("safety", "safety_and_tone.log")
ops_log = setup_custom_logger("ops", "sentinel_ops.log")
prompt_log = setup_custom_logger("prompts", "prompt_history.log")