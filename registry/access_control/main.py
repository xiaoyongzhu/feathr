from smtplib import SMTPRecipientsRefused

import uvicorn
import os
import traceback

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from flask import Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from iam.exceptions import LoginError, ConflictError, EntityNotFoundError, AccessDeniedError
from rbac import config
from api import router as api_router
from iam.config import REGISTRY_DEBUGGING

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


def exc_to_content(e: Exception, parameter_error: bool = False) -> Dict:
    """ In scenarios where the user parameter cannot pass
     parameter_error:False the error will be displayed on the page
     parameter_error:True the error should not be display to the user"""
    if parameter_error:
        content = {"status": "FAILED", "message": str(e)}
    else:
        content = {"status": "PARAMETER_ERROR", "message": str(e)}
    if os.environ.get(REGISTRY_DEBUGGING):
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
