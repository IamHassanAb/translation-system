import threading
import json
import asyncio
import logging
import queue
from fastapi import FastAPI, WebSocket, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from utils.utils import utility_service
from services.status import status_service
from services.response import response_service
# from services.translation import translation_service  # ensure this runs as needed
# from services.language_detection import language_detection  # ensure this runs as needed


import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app : FastAPI):
    await utility_service.start_background_tasks()
    yield
    utility_service.close_background_tasks()
    

app = FastAPI(title="Real-Time Translation Network",lifespan=lifespan)

# Configure CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Utility we will think about 
def get_status_message(timeout=0.5):
    try:
        return status_service.status_message_queue.get(timeout=timeout)
    except queue.Empty:
        return None


@app.get("/")
async def root():
    logger.info("Root endpoint accessed.")
    return {"message": "Real-Time Translation Network API"}

@app.get("/status")
def send_status():
    logger.info("Sending status message...")
    try:
        # Attempt to get a message without blocking
        message = status_service.status_message_queue.get_nowait()
        return message
    except queue.Empty:
        logger.info("Status message queue is empty.")
        return {"status": "No status message available."}
    # message = get_status_message()

@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connection established for room: {room_id}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message: {data} in room: {room_id}")
            message = json.loads(data)
            message['id'] = 1
            response = await utility_service.start_langauge_detection(message)
            logger.info("Response from language detection service: %s", response)

            try:
                loop = asyncio.get_running_loop()
                message = await loop.run_in_executor(None, response_service.translation_response_queue.get)
            except asyncio.CancelledError:
                logger.info("WebSocket task was cancelled during shutdown.")
                raise  # Important: re-raise it so FastAPI can shut down cleanly
            except queue.Empty:
                logger.warning("Translation response queue is empty.")
                message = {"error": "No translation response available."}
            except Exception as e:
                logger.error(f"Error while processing translation response: {e}")
                message = {"error": "An error occurred while processing the translation response."}


            print("----- RESP: {}".format(message))
            # Process the message (kick off the pipeline)
            await websocket.send_json(message)
    except Exception as e:
        logger.error(f"Error in websocket: {e}")
        if not websocket.client_state.name == "DISCONNECTED":
            try:
                await websocket.close()
            except RuntimeError as close_err:
                logger.warning(f"WebSocket already closed: {close_err}")
    finally:
        logger.info(f"WebSocket connection closed for room: {room_id}")

if __name__ == "__main__":

    logger.info("Starting FastAPI application...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000)