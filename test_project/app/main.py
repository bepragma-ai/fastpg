import logging
import time
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router

from fastpg.core import (
    ASYNC_DB_READ,
    ASYNC_DB_WRITE,
)


root_router = APIRouter()
app = FastAPI(
    title='FastPG Test'
)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await ASYNC_DB_READ.connect()
    print("READ DB successfully connected...")
    await ASYNC_DB_WRITE.connect()
    print("WRITE DB successfully connected...")


@app.on_event("shutdown")
async def shutdown():
    await ASYNC_DB_READ.close()
    print("READ DB successfully disconnected...")
    await ASYNC_DB_WRITE.close()
    print("WRITE DB successfully disconnected...")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/health")
def health():
    return {"data":{"message":"I'm up!"},"success":True,"error":None}


app.include_router(api_router)
app.include_router(root_router)
