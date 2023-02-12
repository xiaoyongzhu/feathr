from smtplib import SMTPRecipientsRefused

import uvicorn
import os
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from flask import Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from iam.exceptions import LoginError, ConflictError, EntityNotFoundError, AccessDeniedError
from rbac import config
from api import router as api_router


from typing import Dict

rp = "/"
try:
    rp = config.RBAC_API_BASE
    if rp[0] != '/':
        rp = '/' + rp
except:
    pass

def get_application() -> FastAPI:
    application = FastAPI()
    # Enables CORS
    application.add_middleware(CORSMiddleware,
                               allow_origins=["*"],
                               allow_credentials=True,
                               allow_methods=["*"],
                               allow_headers=["*"],
                               )

    application.include_router(prefix=rp, router=api_router)
    return application


app = get_application()


def exc_to_content(e: Exception) -> Dict:
    """ In scenarios where the user parameter cannot pass, the error will be displayed on the page """
    content = {"status": "FAILED", "message": str(e)}
    if os.environ.get("REGISTRY_DEBUGGING"):
        content["traceback"] = "".join(traceback.TracebackException.from_exception(e).format())
    return content


def exc_to_parameter_error_content(e: Exception) -> Dict:
    """ In scenarios where there is an error with the parameters being transmitted from the front-end,
    the error should not be display to the user """
    print(e)
    content = {"status": "PARAMETER_ERROR", "message": str(e)}
    if os.environ.get("REGISTRY_DEBUGGING"):
        content["traceback"] = "".join(traceback.TracebackException.from_exception(e).format())
    return content


@app.exception_handler(RequestValidationError)
async def http_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(str(exc)),
    )


@app.exception_handler(ConflictError)
async def conflict_error_handler(_, exc: ConflictError):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(exc),
    )


@app.exception_handler(EntityNotFoundError)
async def conflict_error_handler(_, exc: EntityNotFoundError):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(exc),
    )


@app.exception_handler(LoginError)
async def conflict_error_handler(_, exc: LoginError):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(exc),
    )


@app.exception_handler(AccessDeniedError)
async def conflict_error_handler(_, exc: AccessDeniedError):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(exc),
    )


@app.exception_handler(SMTPRecipientsRefused)
async def conflict_error_handler(_, exc: SMTPRecipientsRefused):
    return JSONResponse(
        status_code=200,
        content=exc_to_content(exc),
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
