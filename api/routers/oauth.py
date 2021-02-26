from datetime import datetime
from urllib.parse import parse_qs

import asyncpg
from aiohttp import ClientSession
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
    templating,
)
from jose import jwt

from config.common import config
from config.oauth import github_oauth_config, stack_oauth_config

from ..dependencies import aiohttp_session, db_connection, jinja, state_check

router = APIRouter(
    prefix="/oauth",
)

# {table} is the table name, {field} the field name
# Hence this query is safe against sql injection type attacks
insert_or_update_template = """
insert into {table} (id, {field}) values ($1, $2) on conflict (id) do update set {field}=$2
""".strip()

stack_sql_query = insert_or_update_template.format(
    table="users", field="stackoverflow_oauth_token"
)
github_sql_query = insert_or_update_template.format(
    table="users", field="github_oauth_token"
)


# TODO: Cache recently used jwt tokens until expiry and deny their usage
# TODO: Serverless is stateless, hence use db caching


@router.get("/stackexchange")
async def stackexchange_oauth(
    request: Request,
    code: str = Query(...),
    user_id: int = Depends(state_check),
    db_conn: asyncpg.pool.Pool = Depends(db_connection),
    session: ClientSession = Depends(aiohttp_session),
):
    """Link account with stackexchange through OAuth2"""

    res = await session.post(
        "https://stackoverflow.com/oauth/access_token/json",
        data={**stack_oauth_config.dict(), "code": code},
    )
    auth = await res.json()
    if "access_token" not in auth:
        return {k: v for k, v in auth.items() if k.startswith("error_")}
    await db_conn.execute(stack_sql_query, user_id, auth["access_token"])

    return jinja.TemplateResponse(
        "oauth_success.html", {"request": request, "oauth_provider": "Stackexchange"}
    )


@router.get("/github")
async def github_oauth(
    request: Request,
    code: str = Query(...),
    user_id: int = Depends(state_check),
    db_conn: asyncpg.pool.Pool = Depends(db_connection),
    session: ClientSession = Depends(aiohttp_session),
):
    """Link account with github through OAuth2"""
    res = await session.post(
        "https://github.com/login/oauth/access_token",
        data={**github_oauth_config.dict(), "code": code},
    )
    auth = await res.json()
    await db_conn.execute(github_sql_query, user_id, auth["access_token"])

    return jinja.TemplateResponse(
        "oauth_success.html", {"request": request, "oauth_provider": "Github"}
    )
