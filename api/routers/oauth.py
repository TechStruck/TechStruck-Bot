from fastapi import HTTPException, status
from datetime import datetime
from urllib.parse import parse_qs

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, Query
from jose import jwt

from ..dependencies import aiohttp_session
from config.oauth import github_oauth_config, stack_oauth_config
from config.common import config
from models import UserModel

router = APIRouter(prefix="/oauth", )


async def state_check(state: str = Query(...)) -> UserModel:
    try:
        payload = jwt.decode(state, config.secret)
    except jwt.JWTError:
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "Invalid state")
    user_id = payload['id']
    expiry = payload['expiry']
    if datetime.now() > datetime.fromisoformat(expiry):
        raise HTTPException(status.HTTP_406_NOT_ACCEPTABLE, "Too late")
    user, _ = await UserModel.get_or_create(id=user_id)
    yield user
    await user.save(update_fields=['stackoverflow_oauth_token'])


@router.get("/stackexchange")
async def stackexchange_oauth(
    code: str = Query(...),
    user: UserModel = Depends(state_check),
    session: ClientSession = Depends(aiohttp_session)
):
    """Link account with stackexchange through OAuth2"""

    async with session.post("https://stackoverflow.com/oauth/access_token", data={**stack_oauth_config.dict(), "code": code}) as res:
        auth = parse_qs(await res.text())

    user.stackoverflow_oauth_token = auth['access_token'][0]
    return "Done bruh"


@router.get("/github")
async def github_oauth(code: str = Query(...),
                       user: UserModel = Depends(state_check),
                       session: ClientSession = Depends(aiohttp_session)):
    """Link account with github through OAuth2"""
    async with session.post("https://github.com/login/oauth/access_token", data={**github_oauth_config.dict(), "code": code}) as res:
        auth = (await res.text())
    user.github_oauth_token = auth['access_token']
    return "Done bruh"
