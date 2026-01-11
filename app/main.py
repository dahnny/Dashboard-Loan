from fastapi import FastAPI
from app.api.v1.routes import user
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.loan import router as loan_router
from app.api.v1.routes.loanee import router as loanee_router
from app.api.v1.routes.direct_debit import router as dd_router

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

app.include_router(user.router, prefix="/api/v1", tags=["users"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(loan_router, prefix="/api/v1")
app.include_router(loanee_router, prefix="/api/v1")
app.include_router(dd_router, prefix="/api/v1")