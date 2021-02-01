import sys

from fastapi import Depends, FastAPI, Header, HTTPException, status

if sys.version_info[1] < 7:
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()

from .routers import oauth, webhooks

app = FastAPI()

app.include_router(oauth.router)
app.include_router(webhooks.router)
