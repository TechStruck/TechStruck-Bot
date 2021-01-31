from fastapi import FastAPI, Depends, Header, HTTPException, status
from tortoise import Tortoise

from .routers import oauth, webhooks
from tortoise_config import tortoise_config

app = FastAPI()


@app.on_event("startup")
async def connect_db():
    await Tortoise.init(tortoise_config)

app.include_router(oauth.router)
app.include_router(webhooks.router)
