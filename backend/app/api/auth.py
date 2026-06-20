from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.schemas import (
    SendSmsRequest, LoginRequest, AdminLoginRequest,
    ResponseModel
)
from ..services.auth_service import AuthService
from ..utils.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/send-sms", response_model=ResponseModel)
@router.post("/send-code", response_model=ResponseModel)
def send_sms(request: SendSmsRequest, db: Session = Depends(get_db)):
    try:
        result = AuthService.send_sms_code(db, request.phone)
        return success_response(result, f"验证码已发送，测试验证码为123456")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"发送失败: {str(e)}")


@router.post("/login", response_model=ResponseModel)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = AuthService.login_with_sms(db, request.phone, request.code, request.role)
        return success_response(result, "登录成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"登录失败: {str(e)}")


@router.post("/admin-login", response_model=ResponseModel)
def admin_login(request: AdminLoginRequest, db: Session = Depends(get_db)):
    try:
        result = AuthService.admin_login(db, request.phone, request.password)
        return success_response(result, "登录成功")
    except ValueError as e:
        return error_response(400, str(e))
    except Exception as e:
        return error_response(500, f"登录失败: {str(e)}")
