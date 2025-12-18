#!/usr/bin/env python3
import os
import sys
from typing import Any
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from tools import TOOLS
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("GOOGLE_API_KEY not found in environment variables!")
    sys.exit(1)

def initialize_agent() -> Any:
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.7,
        thinking_budget=-1,
    )

    checkpointer = MemorySaver()

    agent = create_agent(
        model=model,
        tools=TOOLS,
        checkpointer=checkpointer,
        system_prompt="You have youtube search, transcript, and comment retrieval abilities. Every time a user inquires about a topic, you must first search for at least 10 videos of the topic (try multiple search queries), then retrieve the trancripts for the videos from the search results that are most relevent (5+ transcripts), then retrieve comments for the same relevent videos to find tips and tricks, and finally deliver your response based solely on the results of these capabilities."
    )
    
    return agent
