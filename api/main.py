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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["OPTIONS", "POST"],
    allow_headers=["*"],
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
async def chat(request: MessageRequest) -> StreamingResponse:
    return StreamingResponse(
        generate_response(request.message),
        media_type="text/plain"
    )

@app.post("/clear")
async def clear_conversation() -> dict[str, str]:
    global thread_id
    thread_id += 1
    return {"status": "cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

