from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response
from app.api.v1.routes import user as organization_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.loan import router as loan_router
from app.api.v1.routes.loanee import router as loanee_router
from fastapi.security import HTTPBearer

from app.core.idempotency import (
    IDEMPOTENCY_HEADER,
    IDEMPOTENT_METHODS,
    load_cached_response,
    store_cached_response,
)
from app.core.config import settings
# from app.api.v1.routes.direct_debit import router as dd_router

app = FastAPI()

security = HTTPBearer()

origins = (
    [origin.strip() for origin in settings.cors_allow_origins.split(",")]
    if settings.cors_allow_origins
    else ["http://localhost:5173", "http://127.0.0.1:5173"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


# @app.middleware("http")
# async def idempotency_middleware(request: Request, call_next):
#     if request.method not in IDEMPOTENT_METHODS:
#         return await call_next(request)
#     if not request.headers.get(IDEMPOTENCY_HEADER):
#         return await call_next(request)

#     body = await request.body()
#     cached = load_cached_response(request, body=body)
#     if cached is not None:
#         return cached

#     response = await call_next(request)
#     if response.status_code >= 400:
#         return response

#     response_body = b""
#     async for chunk in response.body_iterator:
#         response_body += chunk

#     new_response = Response(
#         content=response_body,
#         status_code=response.status_code,
#         headers=dict(response.headers),
#         media_type=response.media_type,
#         background=response.background,
#     )

#     store_cached_response(
#         request,
#         body=body,
#         response=new_response,
#         response_body=response_body,
#     )
#     return new_response

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

app.include_router(organization_router.router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(loan_router, prefix="/api/v1")
app.include_router(loanee_router, prefix="/api/v1")
# app.include_router(dd_router, prefix="/api/v1")