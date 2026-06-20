from fastapi import HTTPException, status
from ..schemas.schemas import ResponseModel


def success_response(data=None, message: str = "success") -> ResponseModel:
    return ResponseModel(
        code=200,
        message=message,
        data=data
    )


def error_response(code: int, message: str, data=None) -> ResponseModel:
    return ResponseModel(
        code=code,
        message=message,
        data=data
    )


def raise_http_exception(code: int, message: str):
    raise HTTPException(
        status_code=status.HTTP_200_OK,
        detail={
            "code": code,
            "message": message
        }
    )


def handle_exception(exc: Exception) -> ResponseModel:
    if isinstance(exc, HTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return ResponseModel(
                code=exc.detail["code"],
                message=exc.detail["message"],
                data=None
            )
        return ResponseModel(
            code=exc.status_code,
            message=exc.detail,
            data=None
        )
    return ResponseModel(
        code=500,
        message=str(exc),
        data=None
    )
