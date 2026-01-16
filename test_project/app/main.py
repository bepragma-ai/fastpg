import os
import logging
from colorlog import ColoredFormatter
import time
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router

from fastpg import ConnectionType, CONNECTION_MANAGER


# ─────────────────────────────
# Logging setup with colorlog
# ─────────────────────────────

LOG_LEVEL = logging.INFO

LOG_FORMAT = (
    "%(log_color)s[%(levelname)s] "
    "%(asctime)s - %(name)s - %(message)s%(reset)s"
)

formatter = ColoredFormatter(
    LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG":    "cyan",
        "INFO":     "green",
        "WARNING":  "yellow",
        "ERROR":    "red",
        "CRITICAL": "bold_red",
    },
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

root_logger = logging.getLogger()      # root logger so all modules inherit
root_logger.handlers = []              # clear default handlers (important)
root_logger.setLevel(LOG_LEVEL)
root_logger.addHandler(handler)

logger = logging.getLogger(__name__)   # module-level logger


# ─────────────────────────────
# FastPG setup
# ─────────────────────────────

CONNECTION_MANAGER.set_databases({
    'default': {
        'TYPE': ConnectionType.WRITE,
        'USER': os.environ.get("POSTGRES_WRITE_USER"),
        'PASSWORD': os.environ.get("POSTGRES_WRITE_PASSWORD"),
        'DB': os.environ.get("POSTGRES_WRITE_DB"),
        'HOST': os.environ.get("POSTGRES_WRITE_HOST"),
        'PORT': os.environ.get("POSTGRES_WRITE_PORT"),
    },
    'replica_1': {
        'TYPE': ConnectionType.READ,
        'USER': os.environ.get("POSTGRES_READ_USER"),
        'PASSWORD': os.environ.get("POSTGRES_READ_PASSWORD"),
        'DB': os.environ.get("POSTGRES_READ_DB"),
        'HOST': os.environ.get("POSTGRES_READ_HOST"),
        'PORT': os.environ.get("POSTGRES_READ_PORT"),
    }
})


# ─────────────────────────────
# FastAPI app setup
# ─────────────────────────────

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


@app.on_event("startup")
async def startup():
    await CONNECTION_MANAGER.connect_all()


@app.on_event("shutdown")
async def shutdown():
    await CONNECTION_MANAGER.close_all()


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
