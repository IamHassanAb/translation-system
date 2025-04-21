from fastapi import FastAPI
# from models.request import Request
# from models.response import Response
from contextlib import asynccontextmanager
from utils.utils import utility_service

@asynccontextmanager
async def lifespan(app : FastAPI):
    await utility_service.start_background_tasks()
    yield
    utility_service.close_background_tasks()

app = FastAPI(title="Translation Service",lifespan=lifespan)



@app.get("/")
def enter():
    return {"message": "Welcome to the Translation Service!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8082)