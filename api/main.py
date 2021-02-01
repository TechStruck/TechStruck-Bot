from fastapi import Depends, FastAPI, Header, HTTPException, status

from .dependencies import db_pool
from .routers import oauth, webhooks

app = FastAPI()


@app.on_event("startup")
async def connect_db():
    await db_pool.__aenter__()


@app.on_event("shutdown")
async def close_db():
    await db_pool.__aexit__()

app.include_router(oauth.router)
app.include_router(webhooks.router)
