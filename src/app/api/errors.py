from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def install_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(_: Request, exc: ValueError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(KeyError)
    async def key_error_handler(_: Request, exc: KeyError):
        return JSONResponse(status_code=404, content={"detail": str(exc.args[0]) if exc.args else "not found"})
