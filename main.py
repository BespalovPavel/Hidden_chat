from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router as page_router
from backend.application.manager import manager
from backend.application.sockets import router as socket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await manager.redis_client.close()
    

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(socket_router)
app.include_router(page_router)
