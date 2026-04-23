import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from agents.adaptive_agent_v7 import AdaptiveBankingAgent 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change this to your React URL later)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent once
agent_service = AdaptiveBankingAgent()

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = [] 

    try:
        while True:
            # Receive JSON from React
            data = await websocket.receive_json()
            user_query = data.get("message")
            
            start_time = time.time()

            # --- SCORE GATE FOR IDENTITY RESOLUTION ---
            docs_with_scores = agent_service.vectorstore.similarity_search_with_relevance_scores(user_query, k=2)
            
            # Logic: If low similarity, treat as personal/greeting
            is_personal = all(score < 0.6 for _, score in docs_with_scores)

            if is_personal:
                rich_input = user_query
            else:
                context = "\n".join([d.page_content for d, _ in docs_with_scores])
                rich_input = f"Context: {context}\nQuestion: {user_query}"

            # --- EXECUTION ---
            # Correcting the syntax for the invoke call
            response = agent_service.executor.invoke({
                "input": rich_input,
                "chat_history": chat_history 
            })

            # Update Memory
            chat_history.append({"role": "user", "content": user_query})
            chat_history.append({"role": "assistant", "content": response["output"]})

            # --- METADATA & RESPONSE ---
            latency = round(time.time() - start_time, 2)

            await websocket.send_json({
                "type": "agent_response",
                "content": response["output"],
                "latency": f"{latency}s"
            })

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        # Graceful Failure Handling (Phase 8 requirement)
        await websocket.send_json({"type": "error", "content": str(e)})