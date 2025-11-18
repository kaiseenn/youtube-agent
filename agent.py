#!/usr/bin/env python3
"""
YouTube Study Assistant - LangChain ReAct Agent
An autonomous agent that searches YouTube, extracts transcripts, and fetches comments
to help with studying and research.
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from tools import TOOLS
load_dotenv()

# Get API key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("❌ ERROR: GOOGLE_API_KEY not found in environment variables!")
    print("Please create a .env file with your Google API key:")
    print("  GOOGLE_API_KEY=your_api_key_here")
    print("\nGet your API key from: https://makersuite.google.com/app/apikey")
    sys.exit(1)

def create_study_assistant():
    """
    Creates and configures the YouTube Study Assistant agent with:
    - Gemini 1.5 Pro model for intelligent reasoning
    - Three tools: search_youtube, get_transcript, get_comments
    - Short-term memory to maintain conversation context
    - ReAct-style reasoning (Thought -> Action -> Observation)
    """
    # Initialize Gemini model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY,
        temperature=0.7
    )
    
    print(f"Available tools: {len(TOOLS)}")
    for tool in TOOLS:
        print(f"      - {tool.name}: {tool.description.split('.')[0]}")

    checkpointer = MemorySaver()

    agent = create_agent(
        model=model,
        tools=TOOLS,
        checkpointer=checkpointer,
    )
    
    return agent


def print_separator(char="─", length=80):
    """Print a separator line."""
    print(char * length)


def run_interactive_session():
    """
    Main interactive loop for the study assistant.
    Handles user input, agent execution, and display of results.
    """
    
    # Initialize agent
    agent = create_study_assistant()
    
    thread_id = 1
    while True:
        try:
            # Get user input
            print("You: ", end="", flush=True)
            user_input = input().strip()
            
            if user_input.lower() in ['clear']:
                thread_id += 1
                print("\n🔄 Starting new conversation (memory cleared)\n")
                print_separator()
                print()
                continue
            
            if not user_input:
                continue
            
            # Prepare configuration with thread ID for memory
            config = {"configurable": {"thread_id": thread_id}}
            
            print()
            print_separator("=")
            print("Gemini: ",end="")
            
            for token, metadata in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages"
            ):
                # Get the latest message
                if not token.content_blocks:
                    continue
                message = token.content_blocks[0]
                type = message["type"]
                if type == "text":
                    print(message["text"],end="")

                if type == "tool_call":
                    print("Calling " + message["name"])
                
            
            print_separator("=")
            print()
        
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue


# ======================================================================================================================
# MAIN ENTRY POINT
# ======================================================================================================================

if __name__ == "__main__":
    try:
        run_interactive_session()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)

