from fastapi import FastAPI
import uvicorn
# from models.request import Request
# from models.response import Response
from contextlib import asynccontextmanager
from services.language_detection import language_detection

@asynccontextmanager
async def lifespan(app : FastAPI):
    yield
    language_detection.close()


app = FastAPI(title="Language Detection Service", lifespan=lifespan)

@app.post("/detect-language")
def detect_language(request : dict):
    response = language_detection.process(request)
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8081, reload=True)