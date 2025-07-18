"""Main agent orchestration for the CodeGen Agent."""
import logging
from google.adk.agents import LlmAgent
from .sub_agents.youtube import youtube_agent

# Configure logging
logger = logging.getLogger(__name__)

# 2. The root agent that orchestrates the entire workflow.
#    It runs the initial code generation, then enters the refinement loop.
root_agent = youtube_agent
