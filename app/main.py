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


from app.api.v1.auth import router as auth_router

# Auth endpoints MUST be public so Swagger can get a token
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
# All other API endpoints require the X-API-KEY
app.include_router(api_router, prefix=settings.API_V1_STR, dependencies=[Depends(get_api_key)])


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="Confess API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "scopes": {},
                    "tokenUrl": f"{settings.API_V1_STR}/auth/token"
                }
            }
        },
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-KEY"
        }
    }

    # Remove global security to allow per-route security (public vs protected) to work
    if "security" in openapi_schema:
        del openapi_schema["security"]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
