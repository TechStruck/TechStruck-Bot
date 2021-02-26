import sys

from fastapi import FastAPI, Request

from .exceptions import CustomHTTPException
from .routers import oauth, webhooks

if sys.version_info[1] < 7:
    from backports.datetime_fromisoformat import MonkeyPatch

    MonkeyPatch.patch_fromisoformat()


app = FastAPI()


@app.exception_handler(CustomHTTPException)
def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
    return exc.response


app.include_router(oauth.router)
app.include_router(webhooks.router)
