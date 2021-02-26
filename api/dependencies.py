import ssl
import hmac
from datetime import datetime

import asyncpg
from aiohttp import ClientSession
from fastapi import Header, HTTPException, Query, Request, status, templating
from jose import jwt

from config.common import config
from config.webhook import webhook_config

from .exceptions import CustomHTTPException

jinja = templating.Jinja2Templates("./public/templates/")


def auth_dep(authorization: str = Header(...)):
    if not hmac.compare_digest(authorization, webhook_config.authorization):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


async def aiohttp_session():
    session = ClientSession(headers={"Accept": "application/json"})
    try:
        yield session
    finally:
        await session.close()


def state_check(request: Request, state: str = Query(...)) -> int:
    try:
        payload = jwt.decode(state, config.secret)
    except jwt.JWTError:
        raise CustomHTTPException(
            jinja.TemplateResponse(
                "oauth_error.html",
                {"request": request, "detail": "Invalid state"},
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )
        )

    expiry = datetime.fromisoformat(payload["expiry"])
    if datetime.now() > expiry:
        raise CustomHTTPException(
            jinja.TemplateResponse(
                "oauth_error.html",
                {"request": request, "detail": "Expired link"},
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
            )
        )

    return payload["id"]


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


async def db_connection():
    connection = await asyncpg.connect(config.database_uri, ssl=ctx)
    try:
        yield connection
    finally:
        await connection.close()
