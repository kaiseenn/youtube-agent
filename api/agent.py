#!/usr/bin/env python3
import os
import sys
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

def initialize_agent():

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

def run_interactive_session():

    agent = initialize_agent()
    
    thread_id = 1
    while True:
        try:
            # Get user input
            print("You: ", end="", flush=True)
            user_input = input().strip()
            
            if user_input.lower() == "clear":
                thread_id += 1
                print("\n🔄 Starting new conversation (memory cleared)\n")
                print()
                continue
            
            if not user_input:
                continue
            
            # Prepare configuration with thread ID for memory
            config = {"configurable": {"thread_id": thread_id}}

            print("Gemini: ",end="")
            
            for token, metadata in agent.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages"
            ):
                # Get the latest message
                if not token.content_blocks:
                    continue
                for message in token.content_blocks:
                    type = message.get("type")
                    if type == "text" and metadata.get("langgraph_node") == "model":
                        print(message["text"],end="")

                    if type == "tool_call":
                        print("Calling " + message["name"] + " with " + str(message["args"]))
        
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
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

