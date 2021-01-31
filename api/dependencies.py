from aiohttp import ClientSession
from fastapi import Header, HTTPException, status

from config.common import config

def auth_dep(authorization:str=Header(...)):
    if authorization != config.authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)


async def aiohttp_session():
    session = ClientSession(headers={"Accept": "application/json"})
    try:
        yield session
    finally:
        await session.close()
