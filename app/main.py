import uvicorn
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.db.sessions import init_db
from app.config.settings import settings
import app.models
from app.config.api_key import get_api_key
from app.api.v1 import router as api_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware




@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    :param app:
    """
    await init_db()
    yield



limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Security Middlewares
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

# app.mount("/static", StaticFiles(directory="uploaded_files"), name="static")


app.include_router(api_router, dependencies=[Depends(get_api_key)])


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
