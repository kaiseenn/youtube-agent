"""Definition of the Code Agent."""
from google.adk.agents import LlmAgent
from search_agent.config import GEMINI_MODEL_LIGHT
from .prompt import YOUTUBE_AGENT_INSTRUCTION
from google.genai import types
from .tools import transcript, comments, search

youtube_agent = LlmAgent(
    name="YoutubeAgent",
    model=GEMINI_MODEL_LIGHT,
    instruction=YOUTUBE_AGENT_INSTRUCTION,
    output_key="youtube_results",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.6
    ),
    tools=[transcript, comments, search]
)
