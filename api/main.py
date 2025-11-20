#!/usr/bin/env python3
import os
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agent import initialize_agent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your actual allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
    )

agent = initialize_agent()
thread_id = 0

class MessageRequest(BaseModel):
    message: str

async def generate_response(user_message: str) -> AsyncGenerator[str, None]:
    global agent, thread_id
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        async for token, metadata in agent.astream(
            {"messages": [HumanMessage(content=user_message)]},
            config=config,
            stream_mode="messages"
        ):
            if not token.content_blocks:
                continue
            
            for message in token.content_blocks:
                msg_type = message.get("type")
            
                if msg_type == "text" and metadata.get("langgraph_node") == "model":
                    yield message["text"]
                elif msg_type == "tool_call":
                    yield f"\n[Calling {message['name']} with {str(message['args'])}]\n"
    except Exception as e:
        yield f"\n[Error: {str(e)}]\n"

@app.post("/chat")
async def chat(request: MessageRequest):
    return StreamingResponse(
        generate_response(request.message),
        media_type="text/plain"
    )

@app.post("/clear")
async def clear_conversation():
    global thread_id
    thread_id += 1
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

